from dataclasses import dataclass
from typing import Tuple, List

import numpy as np
from scipy.interpolate import interp1d
from scipy.signal import savgol_filter
from scipy.stats import norm
from scipy.special import logsumexp


@dataclass
class LCurveResult:
    optimal_kd: float
    kd_error: float
    curvature: np.ndarray
    x_smooth: np.ndarray
    y_smooth: np.ndarray
    change_points: List[float]


class LCurveAnalysis:
    @staticmethod
    def calculate_curvature(
        x: np.ndarray, y: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Calculate curvature of the L-curve in log-log space with improved smoothing"""
        # Convert to log space
        log_x = np.log10(x)
        log_y = np.log10(y)

        # Use fewer points for faster interpolation
        f = interp1d(log_x, log_y, kind="cubic", bounds_error=False)
        x_smooth = np.linspace(log_x.min(), log_x.max(), 500) 
        y_smooth = f(x_smooth)

        window = 21  # Must be odd
        order = 3

        dx = savgol_filter(np.gradient(x_smooth), window, order)
        dy = savgol_filter(np.gradient(y_smooth), window, order)
        d2x = savgol_filter(np.gradient(dx), window, order)
        d2y = savgol_filter(np.gradient(dy), window, order)

        # Calculate curvature with improved numerical stability
        num = np.abs(dx * d2y - dy * d2x)
        denom = (dx * dx + dy * dy) ** 1.5
        curvature = np.where(denom > 1e-10, num / denom, 0)

        return x_smooth, y_smooth, curvature

    @staticmethod
    def bayesian_change_point(x: np.ndarray, y: np.ndarray, max_points: int = 3) -> List[int]:
        """Detect change points using optimized Bayesian inference"""
        n = len(x)
        window_size = min(20, n // 4)  # Adaptive window size
        min_separation = window_size // 2  # Minimum distance between change points
        change_points = []
        
        # Calculate local statistics using sliding window
        local_scores = np.zeros(n - window_size)
        for i in range(len(local_scores)):
            segment = y[i:i + window_size]
            mu = np.mean(segment)
            sigma = np.std(segment) + 1e-8
            local_scores[i] = np.sum(norm.logpdf(segment, mu, sigma))

        # Find potential change points using local score differences
        score_diff = np.abs(np.gradient(local_scores))
        threshold = np.mean(score_diff) + 2 * np.std(score_diff)
        
        # Get candidate change points
        candidates = np.where(score_diff > threshold)[0]
        
        # Filter candidates based on minimum separation
        if len(candidates) > 0:
            filtered_points = [candidates[0]]
            for point in candidates[1:]:
                if point - filtered_points[-1] >= min_separation:
                    filtered_points.append(point)
                if len(filtered_points) >= max_points:
                    break
            
            change_points = sorted(filtered_points)

        return change_points

    @staticmethod
    def analyze(kd_values: np.ndarray, chi2_values: np.ndarray) -> LCurveResult:
        """Perform L-curve analysis using Bayesian change point detection"""
        x_smooth, y_smooth, curvature = LCurveAnalysis.calculate_curvature(
            kd_values, chi2_values
        )

        # Apply smoothing to curvature
        curvature_smooth = savgol_filter(curvature, 51, 3)

        # Detect change points in curvature
        change_points = LCurveAnalysis.bayesian_change_point(x_smooth, curvature_smooth)

        # Find region with maximum curvature
        max_curv_idx = np.nanargmax(curvature_smooth)
        optimal_kd = 10 ** x_smooth[max_curv_idx]

        # Use change points to define transition region
        cp_before = max([cp for cp in change_points if cp < max_curv_idx], default=0)
        cp_after = min([cp for cp in change_points if cp > max_curv_idx], default=len(x_smooth)-1)
        
        # Extract transition region
        transition_region = curvature_smooth[cp_before:cp_after]
        transition_x = x_smooth[cp_before:cp_after]

        # Calculate weighted error based on curvature in transition region
        weights = transition_region / np.max(transition_region)
        weighted_mean = np.average(transition_x, weights=weights)
        weighted_std = np.sqrt(
            np.average((transition_x - weighted_mean) ** 2, weights=weights)
        )

        # Convert from log space to linear space for error
        kd_error = (10**weighted_std - 1) * optimal_kd

        return LCurveResult(
            optimal_kd=optimal_kd,
            kd_error=kd_error,
            curvature=curvature_smooth,
            x_smooth=x_smooth,
            y_smooth=y_smooth,
            change_points=[10 ** x_smooth[cp] for cp in change_points]
        )

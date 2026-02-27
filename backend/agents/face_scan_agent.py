"""
Face Scan Agent
Thin wrapper that delegates directly to the FacialAnalysisClient.
No LangGraph, no Gemini — just HTTP calls to cannon_facial_analysis.
"""

from models.scan import ScanAnalysis
from services.facial_analysis_client import facial_analysis_client


class FaceScanAgent:
    """Delegates face scan analysis to the cannon_facial_analysis microservice."""

    async def analyze_video(self, video_data: bytes, filename: str = "scan.mp4") -> ScanAnalysis:
        """
        Upload a raw video to the cannon_facial_analysis service.
        The service extracts frames, runs analysis, and returns results.
        """
        return await facial_analysis_client.upload_video(video_data, filename)

    async def analyze(
        self,
        front_image: bytes,
        left_image: bytes,
        right_image: bytes
    ) -> ScanAnalysis:
        """
        Analyze three pre-extracted face images (front, left, right).
        Sends them as base64 JSON frames to the analysis service.
        """
        return await facial_analysis_client.analyze_frames([front_image, left_image, right_image])


# Singleton
face_scan_agent = FaceScanAgent()

import cv2
import json
import numpy as np
from pathlib import Path
from typing import Dict, Any, List

from .yolo_model import YoloModel
from .llava_model import LlavaModel
from ..commons.logger import Logger
from ..config.config import ModelConfig

logger = Logger()


class VisionPipeline:
    def __init__(self, config: ModelConfig, max_frames: int = 5):
        self.yolo = YoloModel(config)
        self.llava = LlavaModel(config)
        self.max_frames = max_frames

    def analyze(
        self,
        image_path: Path,
        conf: float = 0.5,
        prompt: str = "Describe what you see in this image.",
        system_prompt: str = "",
    ) -> Dict[str, Any]:
        # Check if it's a video file
        if image_path.suffix.lower() in ['.mp4', '.avi', '.mov', '.mkv', '.webm']:
            return self._analyze_video(image_path, conf, prompt, system_prompt)
        else:
            return self._analyze_image(image_path, conf, prompt, system_prompt)

    def _analyze_image(
        self,
        image_path: Path,
        conf: float = 0.5,
        prompt: str = "Describe what you see in this image.",
        system_prompt: str = "",
    ) -> Dict[str, Any]:
        image = cv2.imread(str(image_path))
        if image is None:
            logger.error(f"Failed to load image from: {image_path}")
            return {"error": "Image not found or unreadable"}

        yolo_detections = self.yolo.detect(image, conf)
        llava_description = self.llava.analyze(image, prompt, system_prompt)

        combined_result = {
            "image_path": str(image_path),
            "scene_description": llava_description,
            "detections": yolo_detections,
            "media_type": "image"
        }

        self._save_results(combined_result, image_path)
        return combined_result

    def _analyze_video(
        self,
        video_path: Path,
        conf: float = 0.5,
        prompt: str = "Describe what you see in this video.",
        system_prompt: str = "",
    ) -> Dict[str, Any]:
        """Extract frames from video and analyze them"""
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            logger.error(f"Failed to open video: {video_path}")
            return {"error": "Video not found or unreadable"}

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        duration = total_frames / fps if fps > 0 else 0

        # Calculate frame indices to extract (evenly distributed)
        frame_indices = self._get_frame_indices(total_frames, self.max_frames)
        
        frame_results = []
        all_detections = []
        all_descriptions = []

        for i, frame_idx in enumerate(frame_indices):
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            
            if not ret:
                logger.warning(f"Failed to read frame {frame_idx} from video")
                continue

            # Analyze this frame
            yolo_detections = self.yolo.detect(frame, conf)
            llava_description = self.llava.analyze(frame, f"{prompt} (Frame {i+1}/{len(frame_indices)})", system_prompt)

            frame_result = {
                "frame_number": frame_idx,
                "timestamp": frame_idx / fps if fps > 0 else 0,
                "detections": yolo_detections,
                "description": llava_description
            }
            frame_results.append(frame_result)
            all_detections.extend(yolo_detections)
            all_descriptions.append(llava_description)

        cap.release()

        # Combine all frame descriptions
        combined_description = self._combine_descriptions(all_descriptions)

        combined_result = {
            "video_path": str(video_path),
            "total_frames": total_frames,
            "duration": duration,
            "fps": fps,
            "frames_analyzed": len(frame_results),
            "frame_results": frame_results,
            "scene_description": combined_description,
            "detections": all_detections,
            "media_type": "video"
        }

        self._save_results(combined_result, video_path)
        return combined_result

    def _get_frame_indices(self, total_frames: int, max_frames: int) -> List[int]:
        """Get evenly distributed frame indices"""
        if total_frames <= max_frames:
            return list(range(total_frames))
        
        # Get evenly distributed frames
        step = total_frames // max_frames
        indices = [i * step for i in range(max_frames)]
        
        # Ensure we don't exceed total frames
        indices = [min(idx, total_frames - 1) for idx in indices]
        
        return indices

    def _combine_descriptions(self, descriptions: List[str]) -> str:
        """Combine multiple frame descriptions into a coherent video description"""
        if not descriptions:
            return "No description available"
        
        if len(descriptions) == 1:
            return descriptions[0]
        
        # Simple combination - can be improved with more sophisticated merging
        combined = f"Video analysis of {len(descriptions)} frames:\n\n"
        for i, desc in enumerate(descriptions, 1):
            combined += f"Frame {i}: {desc}\n\n"
        
        return combined.strip()

    def _save_results(self, result: Dict[str, Any], image_path: Path) -> None:
        output_file = image_path.parent / f"{image_path.stem}_vision_results.json"
        try:
            with open(output_file, "w") as f:
                json.dump(result, f, indent=2)
            logger.info(f"Saved vision results to: {output_file}")
        except Exception as e:
            logger.error(f"Failed to save JSON: {e}")

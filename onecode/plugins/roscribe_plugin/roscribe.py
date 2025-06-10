"""
ROScribe Plugin for OneCodePlant: Natural Language to ROS 2 Code Generation
"""

from ..base_plugin import BasePlugin
from onecode.ai.nlp_processor import NLPProcessor
from pathlib import Path
import json
import os

class ROScribeGenPlugin(BasePlugin):
    """
    ROScribe plugin for natural language to ROS 2 code generation.
    """
    def __init__(self):
        super().__init__()
        self._name = "roscribe_plugin"
        self._description = "Generate ROS 2 Python packages from natural language prompts."
        self._version = "1.0.0"
        self._author = "OneCodePlant Team"
        self._initialized = False
        self.nlp = NLPProcessor()

    def initialize(self) -> bool:
        self._initialized = True
        return True

    def get_commands(self):
        return {
            'gen_roscribe': self.run
        }

    def run(self, prompt: str, yes: bool = False, open_file: bool = False) -> dict:
        """
        Generate a ROS 2 Python package from a natural language prompt.
        """
        # Compose LLM prompt
        llm_prompt = (
            "You are generating a ROS 2 node in Python. Task: {}\n"
            "Return only the code, using rclpy and ROS 2 best practices.\n"
            "Output a Python file for the node and a launch file.\n"
            "Do not include explanations."
        ).format(prompt)
        
        # Call LLM
        code_response = self.nlp.provider.generate_completion(llm_prompt)
        # Parse code blocks (assume two: .py and launch.py)
        py_code, launch_code = self._extract_code_blocks(code_response)
        
        # Ask user before writing files unless --yes
        if not yes:
            print("About to write generated ROS 2 package files. Continue? [y/N]")
            ans = input().strip().lower()
            if ans not in ("y", "yes"):
                return {"status": "cancelled"}
        
        # Write files
        pkg_name = self._suggest_package_name(prompt)
        pkg_dir = Path("generated_packages") / pkg_name
        node_path = pkg_dir / f"{pkg_name}.py"
        launch_dir = pkg_dir / "launch"
        launch_path = launch_dir / f"{pkg_name}_launch.py"
        os.makedirs(launch_dir, exist_ok=True)
        node_path.write_text(py_code)
        launch_path.write_text(launch_code)
        
        # Optionally open in editor
        if open_file:
            os.system(f"code {node_path}")
        
        return {
            "status": "success",
            "package": str(pkg_dir),
            "node_file": str(node_path),
            "launch_file": str(launch_path)
        }

    def _extract_code_blocks(self, response: str):
        """Extract Python and launch code blocks from LLM response."""
        import re
        code_blocks = re.findall(r"```(?:python)?\n([\s\S]+?)```", response)
        if len(code_blocks) >= 2:
            return code_blocks[0], code_blocks[1]
        elif len(code_blocks) == 1:
            return code_blocks[0], ""
        else:
            # fallback: treat all as python
            return response, ""

    def _suggest_package_name(self, prompt: str) -> str:
        import re
        words = re.findall(r"\w+", prompt.lower())
        return "_".join(words[:5])

    @property
    def name(self):
        return self._name

    @property
    def description(self):
        return self._description

    def get_metadata(self):
        return {
            'name': self.name,
            'version': self._version,
            'description': self.description,
            'author': self._author
        }

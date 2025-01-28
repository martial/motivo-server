# Prediction interface for Cog ⚙️
# https://cog.run/python

from cog import BasePredictor, Input, Path
import os
import time
import subprocess
import requests
from pathlib import Path as PathLib  # Renamed to avoid confusion

def downloader():
    # Create data directory if it doesn't exist
    data_dir = PathLib("data")
    data_dir.mkdir(exist_ok=True)
    
    zip_path = data_dir / "vibe_data.zip"
    
    # verify if the file exists
    if not zip_path.exists():
        print("Downloading model file")
        # download the file
        url = "https://stableai-space.fra1.digitaloceanspaces.com/screen-club/vibe_data.zip"
        r = requests.get(url, allow_redirects=True)
        
        # Write the content to file
        zip_path.write_bytes(r.content)
        print("File downloaded")
        
        # unzip the file using zipfile instead of os.system
        import zipfile
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(data_dir)
        print("File extracted")
    else:
        print("File already exists")


class Predictor(BasePredictor):
    def setup(self) -> None:
        """Load the model into memory to make running multiple predictions efficient"""
        downloader()

    def predict(
        self,
        image: Path = Input(description="Input video file"),  # Changed to cog.Path
        scale: float = Input(
            description="Factor to scale image by", ge=0, le=10, default=1.5
        ),
    ) -> str:
        """Run a single prediction on the model"""
        import torch
        print(torch.__version__)
        print(torch.version.cuda)

        # Create output directory if it doesn't exist
        if not os.path.exists("data/vibe_data/"):
            os.makedirs("data/vibe_data/")
        
        command = f"python ./scripts/demo.py --vid_file {str(image)} --output_folder output/"
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        # Print output in real-time
        while True:
            output = process.stdout.readline()
            error = process.stderr.readline()
            
            if output:
                print(output.strip())
            if error:
                print(error.strip())
                
            # Check if process has finished
            if output == '' and error == '' and process.poll() is not None:
                break
        
        return_code = process.poll()
        return return_code
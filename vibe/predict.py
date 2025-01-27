# Prediction interface for Cog ⚙️
# https://cog.run/python

from cog import BasePredictor, Input, Path
import os
import time
import subprocess


class Predictor(BasePredictor):
    def setup(self) -> None:
        """Load the model into memory to make running multiple predictions efficient"""
        # self.model = torch.load("./weights.pth")

    def predict(
        self,
        image: Path = Input(description="Grayscale input image"),
        scale: float = Input(
            description="Factor to scale image by", ge=0, le=10, default=1.5
        ),
    ) -> str:
        """Run a single prediction on the model"""
        import torch
        print(torch.__version__)
        print(torch.version.cuda)
        #return ""
        # execute command python demo.py --vid_file sample_video.mp4 --output_folder output/ --display
       #time.sleep(500)
        command = f"python ./scripts/demo.py --vid_file {image} --output_folder output/"
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

        # processed_input = preprocess(image)
        # output = self.model(processed_image, scale)
        # return postprocess(output)

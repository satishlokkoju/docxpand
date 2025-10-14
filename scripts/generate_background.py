import os
import json
import base64
import argparse
import typing as tp
from urllib.request import Request, urlopen
from docxpand.image import Image


def main(args):
    headers: tp.Dict[str, str] = {"Content-Type": "application/json"}
    parameters = {
        "prompt": args.prompt,
        "negative_prompt": "blurry, low quality",
        "steps": 20,
        "sampler_name": "DPM++ 2M Karras",
        "cfg_scale": 7,
        "width": 512,
        "height": 512,
        "batch_size": 1,
        "n_iter": 1,
        "seed": -1
    }
    # url = self.get_sdapi_url_from_hostname_port(url)
    url = "http://127.0.0.1:7860/sdapi/v1"

    # Call txt2img with custom prompt
    request = Request(
        url=f"{url}/txt2img",
        headers=headers,
        data=json.dumps(parameters).encode("utf-8"),
    )
    print(f'Making request to: {request.full_url}')
    
    try:
        response_data = urlopen(request).read().decode("utf-8")
        response = json.loads(response_data)
        print('Response received successfully')
    except Exception as e:
        print(f'Error making request: {e}')
        print(f'URL: {request.full_url}')
        raise

    # We asked only for one image, decoding it using OpenCV
    image = Image.from_buffer(base64.b64decode(response["images"][0]))
    print('Saving generated background image to out dir.')
    
    # Ensure output directory exists
    os.makedirs('out', exist_ok=True)
    image.write(args.out_file)



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Generate background images for documents using Stable Diffusion")
    parser.add_argument('--prompt', type=str, required=True)
    parser.add_argument('--out_file', type=str, default='out/background.jpg')
    args = parser.parse_args()
    main(args)
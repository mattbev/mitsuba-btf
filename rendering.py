import argparse
import os

import drjit as dr
import mitsuba as mi

parser = argparse.ArgumentParser()
parser.add_argument(
    "-i",
    "--input",
    type=str,
    default="scenes/simple_sphere/simple_sphere.xml",
    help="Input scene filepath (.xml)",
)
parser.add_argument(
    "-o",
    "--output",
    type=str,
    default="rendered.jpg",
    help="Output image filepath (.jpg, .png)",
)
parser.add_argument(
    "-m",
    "--mode",
    type=str,
    default="scalar_rgb",
    help="Rendering mode (scalar_rgb or gpu_rgb)",
)
args = parser.parse_args()

mi.set_variant(args.mode)
print(mi.variants())

from mitsuba_btf import MeasuredBTF



def main():
    # Register MeasuredBTF
    mi.register_bsdf("measuredbtf", lambda props: MeasuredBTF(props))

    # Filename
    filename_src = args.input
    filename_dst = args.output

    # Load an XML file
    mi.Thread.thread().file_resolver().append(os.path.dirname(filename_src))
    scene = mi.load_file(filename_src)

    # Rendering
    mi.render(scene)
    # scene.integrator().render(scene, scene.sensors()[0])

    # Save image
    film = scene.sensors()[0].film()
    bmp = film.bitmap(raw=True)
    bmp.convert(
        mi.Bitmap.PixelFormat.RGB, 
        mi.Struct.Type.UInt8, 
        srgb_gamma=True
    ).write(
        filename_dst
    )


if __name__ == "__main__":
    main()

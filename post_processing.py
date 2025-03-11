import sox
import argparse

class AudioPostProcessor:
    def __init__(self):
        self.tfm = sox.Transformer()

    def apply_effects(self):
        self.tfm.bandreject(50, 40)
        self.tfm.bandreject(150, 30)
        self.tfm.bandreject(250, 10)

        self.tfm.highpass(frequency=35)

        self.tfm.equalizer(frequency=60, width_q=0.5, gain_db=3)

    def process_file(self, input_file, output_file):
        self.tfm.build(input_file, output_file)
        print(f"Processed {input_file} and saved to {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process an audio file.")
    parser.add_argument("input_file", help="The input audio file")
    parser.add_argument("output_file", help="The output audio file")
    args = parser.parse_args()

    processor = AudioPostProcessor()
    processor.apply_effects()
    processor.process_file(args.input_file, args.output_file)


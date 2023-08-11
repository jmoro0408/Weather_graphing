from pathlib import Path
from typing import Union

import requests

urls = {
    "tmax": r"https://www.metoffice.gov.uk/pub/data/weather/uk/climate/datasets/Tmax/date/UK.txt",
    "tmin": r"https://www.metoffice.gov.uk/pub/data/weather/uk/climate/datasets/Tmin/date/UK.txt",
    "tmean": r"https://www.metoffice.gov.uk/pub/data/weather/uk/climate/datasets/Tmean/date/UK.txt",
    "sunshine": r"https://www.metoffice.gov.uk/pub/data/weather/uk/climate/datasets/Sunshine/date/UK.txt",
    "rainfall": r"https://www.metoffice.gov.uk/pub/data/weather/uk/climate/datasets/Rainfall/date/UK.txt",
}


def grab_url_text_data(url: str, save_text_dir: Union[Path, str]) -> None:
    """

    Args:
        url (str): url to grab text data from, should direct to a .txt html
        e.g "http://www.gutenberg.org/files/11/11-0.txt"
        save_text_dir (Union[Path, str]): directory to save text data in .

    Returns:
    """

    response = requests.get(url)
    response.raise_for_status()
    response.encoding = "UTF-8"
    with open(save_text_dir, "w", encoding="utf-8") as f:
        f.write(response.text)
    print(f"Success! URL {url} data successfully written to {save_text_dir}")
    return None

def main():
    for key, url in urls.items():
        SAVE_DIR = Path(Path.cwd(), "data", f"{key}.txt")
        grab_url_text_data(url, SAVE_DIR)

if __name__ == "__main__":
    main()

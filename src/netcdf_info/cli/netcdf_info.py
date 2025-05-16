import argparse
import sys
from pathlib import Path

import numpy as np
import xarray
from tqdm import tqdm

MIN_HEIGHT = 10000.0
START_YEAR = 2002
STOP_YEAR = 2012
START_DATE = np.datetime64("2002-04-16")
STOP_DATE = np.datetime64("2012-04-13")
def main():
    # define some terminal colors to be used in the help
    colors = {
        "BOLD": "\033[1m",
        "UNDERLINE": "\033[4m",
        "END": "\033[0m",
        "PURPLE": "\033[95m",
        "CYAN": "\033[96m",
        "DARKCYAN": "\033[36m",
        "BLUE": "\033[94m",
        "GREEN": "\033[92m",
        "YELLOW": "\033[93m",
        "RED": "\033[91m",
    }
    # Create the parser
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        prog="netcdf_info",
        description="small helper to get some well defined information from an netcdf file.",
        epilog=f"""
{colors['UNDERLINE']}heights example:{colors['END']}


    """,
    )
    subparsers = parser.add_subparsers(help='subcommands help')
    parser_getaltheightminmax = subparsers.add_parser('getaltheightminmax', help='getaltheightminmax help')
    parser_getaltheightminmax.add_argument("-t", "--textfile", action="store_true", help="text file with files to process")
    parser_getaltheightminmax.add_argument("--c3s", action="store_true", help="filter for c3s")
    parser_getaltheightminmax.add_argument("--summary", action="store_true", help="print station summary")
    parser_getaltheightminmax.add_argument("files", type=Path, nargs="+", help="netcdf files")


    # # Add arguments
    # parser.add_argument(
    #     "getaltheightminmax",
    #     type=bool,
    #     help="print out the min and max heights",
    # )
    # parser.add_argument(
    #     "userfile",
    #     type=Path,
    #     help="user file",
    # )
    # parser.add_argument('-o', '--outdir', type=Path, help='output directory. Defaults to stdout')

    # Parse the arguments
    args = parser.parse_args()

    options = {}
    # options["userfile"] = args.userfile
    # options["outdir"] = args.outdir

    # Because we have sub parsers, only the attributes from the supplied sub parser
    # are part of args
    var = "altitude"
    if sys.argv[1] == "getaltheightminmax":
        options["files"] = args.files
        options["textfile"] = args.textfile
        options["c3s"] = args.c3s
        options["summary"] = args.summary
        if options["textfile"]:
            with open(options["files"][0], "r") as f:
                options["files"] = f.read().splitlines()


        # print("file:min:max")
        ana_data = {}
        stat_data = {}
        max_height = 0.0
        # bar = tqdm(desc="reading files", total=len(options["files"]), disable=None)
        bar = tqdm(desc="reading files", total=len(options["files"]), )
        for _file in options["files"]:
            bar.update(1)
            ana_data[_file] = {}
            if not options["c3s"]:
                df = xarray.open_dataset(_file)
                ana_data[_file]["max"] = df[var].values.max()
                ana_data[_file]["min"] = df[var].values.min()
                ana_data[_file]["statname"] = df.attrs["location"]
                # print(f"{_file}:{df[var].values.min()}:{df[var].values.max()}")
            else:
                # file_year = int(Path(_file).parts[-1].split("_")[-4][0:4])
                df = xarray.open_dataset(_file)
                file_date = df["time"][0].values.astype(np.datetime64)
                # if file_year < START_YEAR or file_year > STOP_YEAR:
                if file_date < START_DATE or file_date > STOP_DATE:
                    continue
                if df[var].values.max() > MIN_HEIGHT:
                    ana_data[_file] = {}
                    ana_data[_file]["max"] = df[var].values.max()
                    ana_data[_file]["min"] = df[var].values.min()
                    ana_data[_file]["statname"] = df.attrs["location"]
                    ana_data[_file]["date"] = df["time"][0].values.astype("datetime64[D]")
                    ana_data[_file]["year"] = int(df["time"].dt.year.values[0])
                    if not ana_data[_file]["statname"] in stat_data:
                        stat_data[df.attrs["location"]] = {}
                        stat_data[df.attrs["location"]]["files"] = []
                        stat_data[df.attrs["location"]]["dates"] = []
                        stat_data[df.attrs["location"]]["days"] = 0
                    try:
                        stat_data[df.attrs["location"]][ana_data[_file]["year"]] += 1
                    except KeyError:
                        stat_data[df.attrs["location"]][ana_data[_file]["year"]] = 1
                    # count days...
                    try:
                        stat_data[df.attrs["location"]]["days"] += 1
                    except KeyError:
                        stat_data[df.attrs["location"]]["days"] = 1


                    stat_data[df.attrs["location"]]["files"].append(_file)
                    stat_data[df.attrs["location"]]["dates"].append(ana_data[_file]["date"])
                    if ana_data[_file]["max"] > max_height:
                        max_height = ana_data[_file]["max"]

                    # print(f"{_file}:{df[var].values.min():.2f}:{df[var].values.max():.2f}")

        if options["summary"]:
            for _stat in stat_data:
                stat_data[_stat]["unique_dates"] = list(set(stat_data[_stat]["dates"]))
                stat_data[_stat]["unique_days"] = len(stat_data[_stat]["unique_dates"])

                print(f"Station: {_stat}")
                for _year in stat_data[_stat]:
                    if _year == "files":
                        liste = ",".join(stat_data[_stat][_year])
                        print(f"    {_year}:{liste}")
                    elif _year == "dates" or _year == "unique_dates":
                        tmp = [str(stat_data[_stat][_year][i]) for i in range(len(stat_data[_stat][_year]))]
                        liste = ",".join(sorted(tmp))
                        print(f"    {_year}:{liste}")
                    else:
                        print(f"    {_year}:{stat_data[_stat][_year]}")
        else:
            for _file in ana_data:
                print(f"{_file}:{ana_data[_file]['statname']}:{ana_data[_file]['min']:.2f}:{ana_data[_file]['max']:.2f}")

        print(f"overall max height: {max_height:.2f}")

if __name__ == "__main__":
    main()

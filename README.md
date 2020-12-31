## bbc-stats
Tooling for the Zogby-Group:
- Syncs data from golfgenius
- Anaylyzes rounds into data files for website

## Install
Run this command to install the `bbc-stats` and `bbc-sync` tools:

```
pip install 'bbc_stats@git+https://github.com/cswelton/bbc-stats@master'
```

Once installed, the `bbc-sync` and `bbc-stats` command line tools will be available:

- `bbc-sync`
```
$ bbc-sync --help
usage: bbc-sync [-h] [--results-output_dir <PATH>] [--disable-screenshots] [--screenshots-output_dir <PATH>] [--filter <REGEX>] [--show-browser] [--quiet]
                [--logfile <PATH>] [--debug]
                <GGID-CODE>

positional arguments:
  <GGID-CODE>           GGID Code to parse. This can be any GGID code from a bbc round.

optional arguments:
  -h, --help            show this help message and exit
  --results-output_dir <PATH>
                        The directory to output result JSON files. (default: ./results)
  --disable-screenshots
                        Turn off screenshots (default: False)
  --screenshots-output_dir <PATH>
                        Directory to store screenshots (default: screenshots)
  --filter <REGEX>      A regular expression to filter round names to parse (default: .*)
  --show-browser        Show the browser as data is being scanned. (default: False)
  --quiet               Do not print logs to the screen. (default: False)
  --logfile <PATH>      Send logs to a file. (default: None)
  --debug               Turn on debug logging. (default: False)
$ 
```

- `bbc-stats`
```
$ bbc-stats --help
usage: bbc-stats [-h] [--results-directory <PATH>] [--weeks <integer>] [--min-rounds <integer>] [--weighted-rounds <integer>] [--outlier-distance <float>]
                 [--weight-birdies <float>] [--weight-scoring <float>] [--weight-pars <float>] [--dump] [--summary] [--player-filter <regex>]
                 [--github-site <PATH>] [--points-flight-winner POINTS_FLIGHT_WINNER] [--points-skin POINTS_SKIN] [--points-nassau-front POINTS_NASSAU_FRONT]
                 [--points-nassau-back POINTS_NASSAU_BACK] [--points-nassau-overall POINTS_NASSAU_OVERALL]

optional arguments:
  -h, --help            show this help message and exit
  --results-directory <PATH>
                        Path to results directory (default: ./results)
  --weeks <integer>     Data range in weeks (default: 4)
  --min-rounds <integer>
                        Minimum number of rounds for player to count in rankings (default: 0)
  --weighted-rounds <integer>
                        Number of recent rounds to weight heavier (default: 2)
  --outlier-distance <float>
                        Distance from median to remove outliers. (default: None)
  --weight-birdies <float>
                        Relative weight to apply to birdies or better per round average. (default: 5)
  --weight-scoring <float>
                        Relative weight to apply to scoring average. (default: 4)
  --weight-pars <float>
                        Relative weight to apply to pars per round average. (default: 2)
  --dump                Dump player data as JSON (default: False)
  --summary             Print data summary before power rankings (default: False)
  --player-filter <regex>
                        Show data for player names that match filter (default: .*)
  --github-site <PATH>  Path to root github site. If set, data will be updated. (default: None)
  --points-flight-winner POINTS_FLIGHT_WINNER
                        Point value for winning flight (ABCD). (default: 1)
  --points-skin POINTS_SKIN
                        Point value for skin. (default: 1)
  --points-nassau-front POINTS_NASSAU_FRONT
                        Point value for winning front 9 nassau bet. (default: 1)
  --points-nassau-back POINTS_NASSAU_BACK
                        Point value for winning back 9 nassau bet. (default: 1)
  --points-nassau-overall POINTS_NASSAU_OVERALL
                        Point value for winning overall nassau bet. (default: 1)
$
```

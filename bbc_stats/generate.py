"""
This script is used to compute the PowerRankings and produce an excel file along with printing to the screen.
"""
from golfgenius.stats import Stats
from bbc_stats.collection import RoundsCollection, PlayersCollection
from bbc_stats.data import GithubData
import json
import datetime
from collections import defaultdict
from operator import itemgetter
import numpy as np
import re
from terminaltables import SingleTable
import xlsxwriter
import os


def json_default_encoder(obj):
    if isinstance(obj, datetime.date):
        return str(obj)
    raise TypeError("Unable to encode %r" % obj)


def parse_args():
    import argparse
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('--results-directory', default='./results', type=str, metavar='<PATH>',
                        help="Path to results directory")
    parser.add_argument('--weeks', type=int, metavar='<integer>',
                        help="Data range in weeks. If not set all rounds are selected.")
    parser.add_argument('--min-rounds', default=0, type=int, metavar='<integer>',
                        help="Minimum number of rounds for player to count in rankings")
    parser.add_argument('--weighted-rounds', default=2, type=int, metavar='<integer>',
                        help="Number of recent rounds to weight heavier")
    parser.add_argument('--outlier-distance', type=float, metavar='<float>',
                        help="Distance from median to remove outliers.")
    parser.add_argument('--weight-birdies', type=float, default=5, metavar='<float>',
                        help="Relative weight to apply to birdies or better per round_info average.")
    parser.add_argument('--weight-scoring', type=float, default=4, metavar='<float>',
                        help="Relative weight to apply to scoring average.")
    parser.add_argument('--weight-pars', type=float, default=2, metavar='<float>',
                        help="Relative weight to apply to pars per round_info average.")
    parser.add_argument('--dump', action='store_true',
                        help="Dump player data as JSON")
    parser.add_argument('--summary', action='store_true',
                        help="Print data summary before power rankings")
    parser.add_argument('--player-filter', type=re.compile, default='.*', metavar='<regex>',
                        help="Show data for player names that match filter")
    parser.add_argument('--github-site', metavar='<PATH>',
                        help="Path to root github site. If set, data will be updated.")
    parser.add_argument('--points-config-file', metavar='<PATH>',
                        help="Path to a JSON file containing points configuration.")
    parser.add_argument('--points-flight-winner', default=1, type=int, help="Point value for winning flight (ABCD).")
    parser.add_argument('--points-skin', default=1, type=int, help="Point value for skin.")
    parser.add_argument('--points-nassau-front', default=1, type=int,
                        help="Point value for winning front 9 nassau bet.")
    parser.add_argument('--points-nassau-back', default=1, type=int,
                        help="Point value for winning back 9 nassau bet.")
    parser.add_argument('--points-nassau-overall', default=1, type=int,
                        help="Point value for winning overall nassau bet.")
    parser.add_argument('--max-rounds-per-month', default=4, type=int,
                        help="Max rounds that count towards points each month.")
    return parser.parse_args()


class PowerRankings(object):
    def __init__(self, results_dir, timedelta=None, weighted_rounds=None, rankings_weights=[1, 1, 1], min_rounds=0):
        """

        :param results_dir: Path to results directory
        :param timedelta: Datetime.timedelta range to limit data
        :param weighted_rounds: How many recent rounds to weight
        :param rankings_weights: Tuple (Scoring, Birdies, Pars)
        :param min_rounds: Minimum number of rounds for player to count in bbc_stats
        """
        self.stats = Stats(results_dir, timedelta=timedelta)
        self.raw_data = self.stats.player_scores()
        self.all_stats = Stats(results_dir, timedelta=None)
        self.weighted_rounds = weighted_rounds
        self.rankings_weights = [float(x) for x in rankings_weights]
        self.min_rounds = min_rounds

    def all_players(self):
        return sorted(self.raw_data.keys())

    def _average_weighted(self, scores):
        weight = 1
        if self.weighted_rounds is None:
            weights = [weight for _ in range(len(scores))]
        else:
            weighted_rounds = int(self.weighted_rounds) if len(scores) >= self.weighted_rounds else len(scores)
            weights = [weight for _ in range(max(0, len(scores) - weighted_rounds))]
            for _ in range(weighted_rounds):
                weight = weight + 1
                weights.append(weight)
                weight = weight * weight
        if not scores:
            return 0.0, 0.0
        return np.average(scores), np.average(scores, weights=weights)

    def scoring_averages(self):
        averages = []
        for player in self.all_players():
            rounds = len(self.raw_data[player])
            if rounds < self.min_rounds:
                continue
            scores = [round["score"] for round in self.raw_data[player]]
            average, weighted = self._average_weighted(scores)
            averages.append((player, average, weighted))
        return sorted(averages, key=itemgetter(2))

    def birdies_or_better_averages(self):
        averages = []
        for player in self.all_players():
            rounds = len(self.raw_data[player])
            if rounds < self.min_rounds:
                continue
            scores = [len(round["eagles"]) + len(round["birdies"]) for round in self.raw_data[player]]
            average, weighted = self._average_weighted(scores)
            averages.append((player, average, weighted))
        return sorted(averages, key=itemgetter(2), reverse=True)

    def par_averages(self):
        averages = []
        for player in self.all_players():
            rounds = len(self.raw_data[player])
            if rounds < self.min_rounds:
                continue
            scores = [len(round["pars"]) for round in self.raw_data[player]]
            average, weighted = self._average_weighted(scores)
            averages.append((player, average, weighted))
        return sorted(averages, key=itemgetter(2), reverse=True)

    def power_rankings(self):
        rankings = defaultdict(dict)
        scoring_averages = self.scoring_averages()
        birdie_averages = self.birdies_or_better_averages()
        par_averages = self.par_averages()
        _all_data = {
            "scoring": [],
            "birdies": [],
            "pars": []
        }
        for player in self.all_players():
            rounds = len(self.raw_data[player])
            if rounds < self.min_rounds:
                continue
            rankings[player]["player"] = player
            rankings[player]["rounds"] = rounds
            for idx, item in enumerate(scoring_averages):
                if item[0] == player:
                    avg, avg_weighted = item[1], item[2]
                    rankings[player]["scoring"] = (idx + 1, avg, avg_weighted)
                    _all_data["scoring"].append(avg_weighted)
            for idx, item in enumerate(birdie_averages):
                if item[0] == player:
                    avg, avg_weighted = item[1], item[2]
                    rankings[player]["birdies"] = (idx + 1, avg, avg_weighted)
                    _all_data["birdies"].append(avg_weighted)
            for idx, item in enumerate(par_averages):
                if item[0] == player:
                    avg, avg_weighted = item[1], item[2]
                    rankings[player]["pars"] = (idx + 1, avg, avg_weighted)
                    _all_data["pars"].append(avg_weighted)
        _all_data["scoring"] = sorted(_all_data["scoring"])
        _all_data["birdies"] = sorted(_all_data["birdies"], reverse=True)
        _all_data["pars"] = sorted(_all_data["pars"], reverse=True)
        for player in rankings.keys():
            _scoring_avg, _scoring_weighted = rankings[player]["scoring"][1], rankings[player]["scoring"][2]
            _birdies_avg, _birdies_weighted = rankings[player]["birdies"][1], rankings[player]["birdies"][2]
            _pars_avg, _pars_weighted = rankings[player]["pars"][1], rankings[player]["pars"][2]
            _scoring_rank = _all_data["scoring"].index(_scoring_weighted) + 1
            _birdies_rank = _all_data["birdies"].index(_birdies_weighted) + 1
            _pars_rank = _all_data["pars"].index(_pars_weighted) + 1
            rankings[player]["scoring"] = _scoring_rank, _scoring_avg, _scoring_weighted
            rankings[player]["birdies"] = _birdies_rank, _birdies_avg, _birdies_weighted
            rankings[player]["pars"] = _pars_rank, _pars_avg, _pars_weighted
            _data = [_scoring_rank, _birdies_rank, _pars_rank]
            rankings[player]["power_ranking"] = 100 / np.average(_data, weights=self.rankings_weights)
        return sorted(rankings.values(), key=itemgetter("power_ranking"), reverse=True)


class RenderOutput(object):
    def __init__(self, parser_args, power_rankings_object):
        self.args = parser_args
        self.pr = power_rankings_object
        today = datetime.datetime.today()
        self.excel = xlsxwriter.Workbook("PowerRankings-{month}-{day}-{year}.xlsx".format(
                month=today.month, day=today.day, year=today.year))

    def render_player_count(self):
        # Player Count Table
        print(SingleTable([["Players"], [len(self.pr.all_players())]], title="Total Players").table)
        worksheet = self.excel.add_worksheet("Total Players")
        worksheet.write(0, 0, "Players")
        worksheet.write_number(0, 1, len(self.pr.all_players()))

    def render_round_count(self):
        # Round Count Table
        round_count_data = [["Rank", "Player", "Rounds"]]
        round_counts = {k: len(v) for k, v in self.pr.raw_data.items()}
        for idx, item in enumerate(sorted(round_counts.items(), key=itemgetter(1), reverse=True)):
            player, rounds = item
            if re.search(self.args.player_filter, player):
                round_count_data.append([idx + 1, player, rounds])
        round_count_table = SingleTable(round_count_data, title="Round Counts")
        print(round_count_table.table)
        col_types = ['number', 'string', 'number']
        sheet = self.excel.add_worksheet("Round Counts")
        row, col = 0, 0
        for header in round_count_data[0]:
            sheet.write(0, col, header)
            col += 1
        row, col = 1, 0
        for row_data in round_count_data[1:]:
            for col_data in row_data:
                getattr(sheet, "write_{}".format(col_types[col]))(row, col, col_data)
                col += 1
            row += 1
            col = 0

    def render_scoring_averages(self):
        # Scoring Average Table
        scoring_averages_data = [["Rank", "Player", "Average", "Trend"]]
        for idx, item in enumerate(self.pr.scoring_averages()):
            player, average, average_weighted = item
            if re.search(self.args.player_filter, player):
                if average_weighted == average:
                    trend = '0'
                elif average_weighted > average:
                    trend = '%.3f' % (average_weighted - average)
                else:
                    trend = '-%.3f' % (average - average_weighted)
                trend = float(trend)
                scoring_averages_data.append((idx + 1, player, "%.3f" % average, "%.3f" % trend))
        scoring_averages_table = SingleTable(scoring_averages_data,
                                             title="Scoring Average")
        print(scoring_averages_table.table)
        sheet = self.excel.add_worksheet("Scoring Average")
        col_types = ['int', 'string', 'float', 'float']
        row, col = 0, 0
        for header in scoring_averages_data[0]:
            sheet.write(row, col, header)
            col += 1
        row, col = 1, 0
        for row_data in scoring_averages_data[1:]:
            for col_data in row_data:
                try:
                    col_type, col_writer = {
                        "int": (lambda d: int(d), 'number'),
                        "float": (lambda d: float(d), 'number'),
                        "string": (lambda d: str(d), 'string')
                    }[col_types[col]]
                    col_data = col_type(col_data)
                    getattr(sheet, "write_{}".format(col_writer))(row, col, col_data)
                except:
                    print("SHEET", "Scoring Average", "ROW", row, "COL", col, "DATA", col_data, "TYPE", type(col_data))
                    raise
                col += 1
            row += 1
            col = 0

    def render_birdies_averages(self):
        # Birdies Per Round Table
        birdies_averages_data = [["Rank", "Player", "Average", "Trend"]]
        for idx, item in enumerate(self.pr.birdies_or_better_averages()):
            player, average, average_weighted = item
            if re.search(self.args.player_filter, player):
                if average_weighted == average:
                    trend = '0'
                elif average_weighted > average:
                    trend = '%.3f' % (average_weighted - average)
                else:
                    trend = '-%.3f' % (average - average_weighted)
                trend = float(trend)
                birdies_averages_data.append((idx + 1, player, "%.3f" % average, "%.3f" % trend))
        birdies_averages_table = SingleTable(birdies_averages_data,
                                             title="Birdies per Round Average")
        print(birdies_averages_table.table)
        sheet = self.excel.add_worksheet("Birdies per Round Average")
        col_types = ['int', 'string', 'float', 'float']
        row, col = 0, 0
        for header in birdies_averages_data[0]:
            sheet.write(row, col, header)
            col += 1
        row, col = 1, 0
        for row_data in birdies_averages_data[1:]:
            for col_data in row_data:
                try:
                    col_type, col_writer = {
                        "int": (lambda d: int(d), 'number'),
                        "float": (lambda d: float(d), 'number'),
                        "string": (lambda d: str(d), 'string')
                    }[col_types[col]]
                    col_data = col_type(col_data)
                    getattr(sheet, "write_{}".format(col_writer))(row, col, col_data)
                except:
                    print("SHEET", "Birdies per Round Average", "ROW", row, "COL", col, "DATA", col_data, "TYPE", type(col_data))
                    raise
                col += 1
            row += 1
            col = 0

    def render_pars_averages(self):
        # Pars Per Round Table
        pars_averages_data = [["Rank", "Player", "Average", "Trend"]]
        for idx, item in enumerate(self.pr.par_averages()):
            player, average, average_weighted = item
            if re.search(self.args.player_filter, player):
                if average_weighted == average:
                    trend = '0'
                elif average_weighted > average:
                    trend = '%.3f' % (average_weighted - average)
                else:
                    trend = '-%.3f' % (average - average_weighted)
                trend = float(trend)
                pars_averages_data.append((idx + 1, player, "%.3f" % average, "%.3f" % trend))
        pars_averages_table = SingleTable(pars_averages_data,
                                          title="Pars per Round Average")
        print(pars_averages_table.table)
        col_types = ['int', 'string', 'float', 'float']
        sheet = self.excel.add_worksheet("Pars per Round Average")
        row, col = 0, 0
        for header in pars_averages_data[0]:
            sheet.write(row, col, header)
            col += 1
        row, col = 1, 0
        for row_data in pars_averages_data[1:]:
            for col_data in row_data:
                try:
                    col_type, col_writer = {
                        "int": (lambda d: int(d), 'number'),
                        "float": (lambda d: float(d), 'number'),
                        "string": (lambda d: str(d), 'string')
                    }[col_types[col]]
                    col_data = col_type(col_data)
                    getattr(sheet, "write_{}".format(col_writer))(row, col, col_data)
                except:
                    print("SHEET", "Pars per Round Average", "ROW", row, "COL", col, "DATA", col_data, "TYPE", type(col_data))
                    raise
                col += 1
            row += 1
            col = 0

    def render_power_rankings(self):
        # Power Rankings Table
        power_rankings_data = [["Rank", "Player", "Power Ranking", "Scoring",
                                "Birdies or Better", "Pars", "Rounds"]]
        for idx, item in enumerate(self.pr.power_rankings()):
            if re.search(self.args.player_filter, item["player"]):
                power_ranking = item["power_ranking"]
                scoring_idx, scoring_avg, scoring_avg_weighted = item["scoring"]
                if scoring_avg_weighted == scoring_avg:
                    scoring_trend = '+-0'
                elif scoring_avg_weighted > scoring_avg:
                    scoring_trend = '+%.3f' % (scoring_avg_weighted - scoring_avg)
                else:
                    scoring_trend = '-%.3f' % (scoring_avg - scoring_avg_weighted)
                birdies_idx, birdies_avg, birdies_avg_weighted = item["birdies"]
                if birdies_avg_weighted == birdies_avg:
                    birdies_trend = '+-0'
                elif birdies_avg_weighted > birdies_avg:
                    birdies_trend = '+%.3f' % (birdies_avg_weighted - birdies_avg)
                else:
                    birdies_trend = '-%.3f' % (birdies_avg - birdies_avg_weighted)
                pars_idx, pars_avg, pars_avg_weighted = item["pars"]
                if pars_avg_weighted == pars_avg:
                    pars_trend = '+-0'
                elif pars_avg_weighted > pars_avg:
                    pars_trend = '+%.3f' % (pars_avg_weighted - pars_avg)
                else:
                    pars_trend = '-%.3f' % (pars_avg - pars_avg_weighted)
                power_rankings_data.append((idx + 1, item["player"], "%.3f" % item["power_ranking"],
                                            "%.3f (%s)" % (scoring_avg_weighted, scoring_trend) if scoring_trend != '+-0' else "%.3f" % scoring_avg_weighted,
                                            "%.3f (%s)" % (birdies_avg_weighted, birdies_trend) if birdies_trend != '+-0' else "%.3f" % birdies_avg_weighted,
                                            "%.3f (%s)" % (pars_avg_weighted, pars_trend) if pars_trend != '+-0' else "%.3f" % pars_avg_weighted,
                                            "%s" % item["rounds"]))
        power_rankings_table = SingleTable(power_rankings_data,
                                           title="Power Rankings")
        print(power_rankings_table.table)
        col_types = ['int', 'string', 'float', 'string', 'string', 'string', 'int']
        sheet = self.excel.add_worksheet("Power Rankings")
        row, col = 0, 0
        for header in power_rankings_data[0]:
            sheet.write(row, col, header)
            col += 1
        row, col = 1, 0
        for row_data in power_rankings_data[1:]:
            for col_data in row_data:
                try:
                    col_type, col_writer = {
                        "int": (lambda d: int(d), 'number'),
                        "float": (lambda d: float(d), 'number'),
                        "string": (lambda d: str(d), 'string')
                    }[col_types[col]]
                    col_data = col_type(col_data)
                    getattr(sheet, "write_{}".format(col_writer))(row, col, col_data)
                except:
                    print("SHEET", "Power Rankings", "ROW", row, "COL", col, "DATA", col_data, "TYPE", type(col_data))
                    raise
                col += 1
            row += 1
            col = 0

    def close(self):
        self.excel.close()

    def update_github_site(self, results_directory, project_root_dir, points_config):
        """
        Updates collections:
            _rounds/<name>.md
            _players/<name>.md
        Updates data:
            players/<name>.json
            rounds/<name>.json
            rankings.json


        :param results_directory: The path to the results directory
        :param project_root_dir: The path to the root of the github pages repo
        :return:
        """
        rounds = RoundsCollection(results_directory, points_config=points_config)
        rounds_data = rounds.export(project_root_dir)
        players = PlayersCollection(results_directory, points_config=points_config)
        players.add_rounds(rounds_data)
        players_data = players.export(project_root_dir)
        data = GithubData(results_directory, stats_obj=self.pr.stats)
        github_data = data.export(project_root_dir)
        points_data = [["Rank", "Points", "Player", "Rounds", "Flight Wins", "Skins", "Overall", "Front", "Back"]]
        for idx, player_data in enumerate(sorted(players_data.values(), key=itemgetter("points"), reverse=True)):
            points_data.append([
                idx + 1,
                player_data["points"],
                player_data["name"],
                player_data["rounds"],
                player_data["flight_wins"],
                player_data["skins"],
                player_data["overall_wins"],
                player_data["front_wins"],
                player_data["back_wins"]
            ])
        points_table = SingleTable(points_data, title="Points")
        print(points_table.table)
        return rounds_data, players_data, github_data



def main():
    args = parse_args()
    if args.weeks is not None:
        timedelta = datetime.timedelta(weeks=args.weeks)
    else:
        timedelta = None
    pr = PowerRankings(args.results_directory, timedelta=timedelta,
                       weighted_rounds=args.weighted_rounds or None,
                       rankings_weights=[args.weight_scoring, args.weight_birdies, args.weight_pars],
                       min_rounds=args.min_rounds)

    out = RenderOutput(args, pr)
    if args.summary:
        out.render_player_count()
        out.render_round_count()
        out.render_scoring_averages()
        out.render_birdies_averages()
        out.render_pars_averages()
    out.render_power_rankings()
    if args.dump:
        data = {}
        for player, rounds in pr.raw_data.items():
            if re.search(args.player_filter, player):
                data[player] = rounds
        print(json.dumps(data, indent=4, default=str, sort_keys=True))
    out.close()
    if args.github_site:
        if args.points_config_file:
            with open(args.points_config_file, "r") as fp:
                points_config = json.load(fp)
        else:
            points_config = {
                "fw": args.points_flight_winner,
                "s": args.points_skin,
                "fr": args.points_nassau_front,
                "ba": args.points_nassau_back,
                "ov": args.points_nassau_overall,
                "max_rounds_per_month": args.max_rounds_per_month
            }
        out.update_github_site(args.results_directory, args.github_site, points_config)

import re
import os
import json
import datetime
import yaml

__version__ = '1.0.0'
MONTH_IDX=['january', 'february', 'march', 'april', 'may', 'june', 'july',
           'august', 'september', 'october', 'november', 'december']


class GithubSiteBase(object):
    output_path = "_data"
    output_format = "yaml"
    output_kwargs = {}

    def __init__(self, results_directory, points_config={"fw": 1, "s": 1, "fr": 1, "ba": 1, "ov": 1 }, stats_obj=None):
        self.rounds = None
        self.players = None
        self.stats = stats_obj
        self.points_config = points_config
        self.results_directory = results_directory
        self.results = {}
        self.round_regexp = re.compile(
            r'Round\s+(?P<round_id>\d+)\s+\((Fri|Sat|Sun|Mon|Tue|Wed|Thu)\,\s+(?P<month>\w+)\s+(?P<day>\d+)\)')
        for f in os.listdir(self.results_directory):
            if f.endswith('.json'):
                with open(os.path.join(self.results_directory, f), 'r') as fp:
                    data = json.load(fp)
                    round_date = self.parse_round_name(data["name"])
                    if round_date is None:
                        print("Unable to find round_info date for round_info %s, assuming today..." % data["name"])
                        round_date = datetime.date.today()
                    data["results"]["date"] = round_date
                    self.results[data["name"]] = data["results"]

    def add_rounds(self, round_data):
        self.rounds = round_data

    def add_players(self, players_data):
        self.players = players_data

    def parse_round_name(self, name):
        # ToDo: Refactor this to support 2021 rounds!!
        m = self.round_regexp.search(name)
        if m:
            round_info = m.groupdict()
            return datetime.date(
                2020,
                MONTH_IDX.index(
                    round_info["month"].lower()) + 1,
                int(round_info["day"]))

    def all_players(self):
        players = set()
        for result in self.results.values():
            for team in result["teams"]:
                for player in team:
                    players.add(player)
        return list(players)

    def parse(self):
        raise NotImplementedError("Base classes must implement parse method.")

    def _write_yaml(self, data, project_root_dir):
        for k, v in data.items():
            with open(os.path.join(project_root_dir, self.output_path, k + ".md"), "w") as fp:
                yaml_str = yaml.dump(v, **self.output_kwargs)
                fp.write("---\n")
                fp.write(yaml_str)
                fp.write("---\n")

    def _write_json(self, data, project_root_dir):
        for k, v in data.items():
            with open(os.path.join(project_root_dir, self.output_path, k + ".json"), "w") as fp:
                json.dump(v, fp, **self.output_kwargs)

    def export(self, project_root_dir):
        data = self.parse(project_root_dir)
        if data:
            if not os.path.isdir(os.path.join(project_root_dir, self.output_path)):
                os.makedirs(os.path.join(project_root_dir, self.output_path), exist_ok=True)
            if self.output_format == "yaml":
                self._write_yaml(data, project_root_dir)
            elif self.output_format == "json":
                self._write_json(data, project_root_dir)
            else:
                raise Exception("Unknown output format: %s" % self.output_format)
        return data

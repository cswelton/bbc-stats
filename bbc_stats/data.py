from bbc_stats import GithubSiteBase
from collections import defaultdict

class GithubData(GithubSiteBase):
    output_path = "_data/player_data"
    output_format = "json"
    output_kwargs = {"indent": 4}

    def parse(self, project_root_dir):
        data = defaultdict(dict)
        player_scores = self.stats.player_scores()
        scoring_averages = dict(self.stats.scoring_averages())
        for player_name, rounds in player_scores.items():
            data[player_name]["name"] = player_name
            if player_name in scoring_averages:
                data[player_name]["scoring_average"] = float("%.3f" % scoring_averages[player_name])
            else:
                data[player_name]["scoring_average"] = 0.000
            data[player_name]["rounds"] = []
            for round in rounds:
                if len(round.get("hole_data", [])) == 18:
                    round_data = {
                        "date": str(round["date"]),
                        "date_timestamp": round["date"].toordinal(),
                        "score": round["score"],
                        "total": round["score"],
                        "name": round["round"],
                        "valid": round["round"] not in self.invalid_rounds,
                        "reason": self.invalid_rounds.get(round["round"]),
                        "front": [round["hole_data"][str(i)] for i in range(1, 10)],
                        "back": [round["hole_data"][str(i)] for i in range(10, 19)],
                        "in": sum([round["hole_data"][str(i)]["score"] for i in range(10, 19)]),
                        "out": sum([round["hole_data"][str(i)]["score"] for i in range(1, 10)])
                    }
                    data[player_name]["rounds"].append(round_data)
        return data

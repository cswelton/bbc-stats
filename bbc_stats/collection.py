from bbc_stats import GithubSiteBase
from operator import itemgetter
from collections import defaultdict
import os
import datetime


class RoundsCollection(GithubSiteBase):
    """
    Updates <root>/_rounds/ with round_info collections...
    Example:
        # Round 59 (Wed, December 23).md
        ---
        name: Round 59 (Wed, December 23)
        date: 2020-04-05
        date_timestamp: 737520
        gg_url: https://golfgenius.com/xxx
        skins:
          Samuel, Matthew:
            - 8
            - 3
          Alford, Sumner:
            - 6
            - 11
            - 5
        flight_winners:
          - Alford, Sumner
          - Welton, Craig
          - Shoffner, Chris
          - Capwell, Robert
        teams:
          - front: false,
            back: true,
            overall: false,
            players:
              - name: Perry, Robbie
                score: 72
              - name: Welton, Craig
                score: 74
              - name: Shoffner, Chris
                score: 76
              - name: Capwell, Robert
                score: 77
        ---
    """
    output_path = "_rounds"
    output_format = "yaml"
    output_kwargs = {}

    def team_best_ball(self, round, hole_range, team, best_ball=2):
        total_scores = []
        for hole in hole_range:
            hole_scores = []
            for player in team:
                if str(hole) in round["scores"][player]["scores"]:
                    hole_scores.append(round["scores"][player]["scores"][str(hole)]["score"])
            total_scores.extend(sorted(hole_scores)[:best_ball])
        return sum(total_scores)

    def parse_teams(self, round):
        teams = []
        for team in round["teams"]:
            teams.append({
                "players": [
                    {
                        "name": player,
                        "score": sum(
                            [x["score"] for x in round["scores"][player]["scores"].values()])
                    } for player in team],
                "front": self.team_best_ball(round, range(1, 10), team),
                "back": self.team_best_ball(round, range(10, 19), team),
                "overall": self.team_best_ball(round, range(1, 19), team)
            })
        front, back, overall = [], [], []
        for team in teams:
            front.append(team["front"])
            back.append(team["back"])
            overall.append(team["overall"])
        front_win = sorted(set(front))[0]
        back_win = sorted(set(back))[0]
        overall_win = sorted(set(overall))[0]
        for team in teams:
            if team["front"] == front_win:
                team["front"] = True
            else:
                team["front"] = False
            if team["back"] == back_win:
                team["back"] = True
            else:
                team["back"] = False
            if team["overall"] == overall_win:
                team["overall"] = True
            else:
                team["overall"] = False
        return teams

    def parse_flight_winners(self, round):
        flights = defaultdict(list)
        for team in round["teams"]:
            for idx, player in enumerate(team):
                if player in round["scores"] and len(round["scores"][player]["scores"]) == 18:
                    flights[idx].append((player, sum([s["score"] for s in round["scores"][player]["scores"].values()])))
        flight_winners = []
        for idx, items in flights.items():
            winning_score = sorted(set([x[1] for x in items]))[0]
            for player, score in items:
                if score == winning_score:
                    flight_winners.append(player)
        return flight_winners

    def parse_skins(self, round):
        hole_scores = defaultdict(list)
        for hole in range(1, 19):
            for player, result in round["scores"].items():
                if str(hole) in result["scores"]:
                    score = result["scores"][str(hole)]["score"]
                    hole_scores[hole].append((player, score))
        skins = defaultdict(list)
        for hole, items in hole_scores.items():
            sorted_items = sorted(items, key=itemgetter(1))
            if sorted_items[0][1] < sorted_items[1][1]:
                skins[sorted_items[0][0]].append(hole)
        return dict(skins)

    def check_round_valid(self, round_name, round_info):
        # Make sure all teams have even number of players
        team_length = 0
        for idx, team in enumerate(round_info["teams"]):
            if idx == 0:
                team_length = len(team)
            elif team_length != len(team):
                print("Skipping round_info %s, teams do not contain equal number of players" % round_name)
                return False, "Teams do not contain equal number of players"
            else:
                team_length = len(team)
        # Makes sure all players have 18 scores posted
        for player_name, info in round_info["scores"].items():
            if len(info["scores"]) != 18:
                print("Skipping round_info %s, not all players finished 18 holes." % round_name)
                return False, "Not all players finished 18 holes"
        return True, None

    def add_points(self, round_data):
        round_data["points"] = {}
        round_data["total_points"] = 0
        for team in round_data["teams"]:
            for player_info in team["players"]:
                player_name = player_info["name"]
                round_data["points"][player_name] = 0
                if player_name in round_data["flight_winners"]:
                    round_data["points"][player_name] += self.points_config["fw"]
                    round_data["total_points"] += self.points_config["fw"]
                for skin in round_data["skins"].get(player_name, []):
                    round_data["points"][player_name] += self.points_config["s"]
                    round_data["total_points"] += self.points_config["s"]
                if team["front"]:
                    round_data["points"][player_name] += self.points_config["fr"]
                    round_data["total_points"] += self.points_config["fr"]
                if team["back"]:
                    round_data["points"][player_name] += self.points_config["ba"]
                    round_data["total_points"] += self.points_config["ba"]
                if team["overall"]:
                    round_data["points"][player_name] += self.points_config["ov"]
                    round_data["total_points"] += self.points_config["ov"]

    def parse(self, project_root_dir):
        data = {}
        for round_name, round in self.results.items():
            valid_round, reason = self.check_round_valid(round_name, round)
            if not valid_round:
                data[round_name] = {
                    "name": round_name,
                    "valid": False,
                    "reason": reason,
                    "date": str(round["date"]),
                    "date_timestamp": round["date"].toordinal(),
                    "gg_url": round.get("gg_url"),
                    "total_points": 0
                }
                continue
            data[round_name] = {
                "name": round_name,
                "valid": True,
                "date": str(round["date"]),
                "date_timestamp": round["date"].toordinal(),
                "gg_url": round.get("gg_url"),
                "teams": self.parse_teams(round),
                "flight_winners": self.parse_flight_winners(round),
                "skins": self.parse_skins(round)
            }
            self.add_points(data[round_name])
        return data


class PlayersCollection(GithubSiteBase):
    output_path = "_players"
    output_format = "yaml"
    output_kwargs = {}

    def generate_points(self, player, target, points_config):
        fw = points_config["fw"]
        s = points_config["s"]
        fr = points_config["fr"]
        ba = points_config["ba"]
        ov = points_config["ov"]
        target["points"] = 0
        target["skins"] = 0
        target["flight_wins"] = 0
        target["front_wins"] = 0
        target["back_wins"] = 0
        target["overall_wins"] = 0
        target["rounds"] = 0
        target["rounds_by_month"] = defaultdict(list)
        target["ignored_rounds"] = []
        target["all_rounds"] = []
        for round_name, round in self.rounds.items():
            round_points = 0
            played = False
            if player in round.get("flight_winners", []):
                target["flight_wins"] += 1
                round_points += fw
            for _ in round.get("skins", {}).get(player, []):
                target["skins"] += 1
                round_points += s
            for team in round.get("teams", []):
                if player in [x["name"] for x in team["players"]]:
                    target["rounds"] += 1
                    played = True
                    if team.get("front"):
                        target["front_wins"] += 1
                        round_points += fr
                    if team.get("back"):
                        target["back_wins"] += 1
                        round_points += ba
                    if team.get("overall"):
                        target["overall_wins"] += 1
                        round_points += ov
            if played:
                round_date = datetime.date.fromordinal(round["date_timestamp"])
                target["rounds_by_month"][round_date.month].append(
                    {
                        "name": round_name,
                        "points": round_points,
                        "date": round_date
                    })
                target["all_rounds"].append({
                    "name": round_name,
                    "points": round_points,
                    "date": round_date
                })
        target["all_rounds"] = sorted(target["all_rounds"], key=itemgetter("date"))
        if points_config["max_rounds_per_month"] > 0:
            for month, rounds in target["rounds_by_month"].items():
                rounds_sorted = sorted(rounds, key=itemgetter("date"), reverse=True)
                _ignored_rounds = []

                if len(rounds_sorted) > points_config["max_rounds_per_month"]:
                    valid_points = sum([r["points"] for r in rounds_sorted[0:points_config["max_rounds_per_month"]]])
                    _ignored_rounds = [r["name"] for r in rounds_sorted[points_config["max_rounds_per_month"]:]]
                    target["ignored_rounds"].extend(_ignored_rounds)
                else:
                    valid_points = sum([r["points"] for r in rounds_sorted])
                target["points"] += valid_points
                for round in rounds:
                    if round["name"] in _ignored_rounds:
                        round["ignored"] = True
                    else:
                        round["ignored"] = False
            target["rounds_by_month"] = dict(target["rounds_by_month"])
        else:
            valid_rounds = self.replace_rounds(target["all_rounds"], points_config["season_round_count"], points_config["replacement_scores"])
            target["points"] = sum([r["points"] for r in valid_rounds])

    def replace_rounds(self, all_rounds, season_round_count, replacement_scores):
        sorted_by_points = sorted(all_rounds[:season_round_count], key=itemgetter("points"))
        extra_rounds = []
        if len(all_rounds) > season_round_count:
            extra_sorted = sorted(all_rounds[season_round_count:], key=itemgetter('points'), reverse=True)
            extra_rounds = extra_sorted[:replacement_scores]
        replaced = []
        for r in extra_rounds:
            for idx, round in enumerate(list(sorted_by_points)):
                if r["points"] > round["points"] and idx not in replaced:
                    replaced.append(idx)
                    sorted_by_points[idx] = r
                    break
        return sorted_by_points

    def parse(self, project_root_dir):
        data = {}
        images_dir = os.path.join(project_root_dir, "assets", "images")
        for player in self.all_players():
            filename = '_'.join([x.strip() for x in player.split(",", 1)])
            if filename + ".png" in os.listdir(images_dir):
                player_image = "/assets/images/%s.png" % filename
            else:
                player_image = "/assets/images/default.png"
            data[filename] = {"name": player, "image": player_image}
            self.generate_points(player, data[filename], self.points_config)

        return data
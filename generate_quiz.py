import pandas as pd, random, time, json
from pathlib import Path
from nba_api.stats.endpoints import (
    leaguegamelog,
    boxscoretraditionalv2,
    boxscoresummaryv2,
    commonplayerinfo
)
from nba_api.stats.static import players
from rapidfuzz import process, fuzz

def generate_and_save_quiz(season="2022-23", save_path="quiz_data"):
    df_conf = pd.read_csv("cbb25.csv")[['Team', 'CONF']].copy()
    df_conf['Cleaned'] = (
        df_conf['Team']
        .str.lower()
        .str.replace(r"[^\w\s]", "", regex=True)
        .str.replace("university of ", "")
        .str.replace("univ. of ", "")
        .str.replace("at ", "")
        .str.replace("the ", "")
        .str.replace("st.", "state")
        .str.replace("st ", "state ")
        .str.replace("state.", "state")
        .str.replace("-", " ")
        .str.replace(".", "")
        .str.replace("(", "")
        .str.replace(")", "")
        .str.strip()
    )

    def clean_school_name(name):
        return (
            name.lower()
            .replace("university of ", "")
            .replace("univ. of ", "")
            .replace("at ", "")
            .replace("the ", "")
            .replace("st.", "state")
            .replace("st ", "state ")
            .replace("state.", "state")
            .replace("-", " ")
            .replace(".", "")
            .replace("(", "")
            .replace(")", "")
            .strip()
        ) if name else ""

    def match_college_to_conf(college_name):
        OVERRIDES = {
            "Texas": ("Texas", "College", "B12"),
            "Southern California": ("Southern California", "College", "P12"),
        }
        if college_name in OVERRIDES:
            return OVERRIDES[college_name]
        if not college_name or college_name.lower().strip() in ["unknown", "none", ""]:
            return "Unknown", "Other", "Other"
        cleaned_input = clean_school_name(college_name)
        result = process.extractOne(cleaned_input, df_conf["Cleaned"], scorer=fuzz.token_sort_ratio)
        if result and result[1] >= 75:
            matched_row = df_conf[df_conf["Cleaned"] == result[0]].iloc[0]
            return matched_row["Team"], "College", matched_row["CONF"]
        if any(word in cleaned_input for word in ["high", "prep", "academy", "charter", "school"]):
            return college_name.title(), "High School", "Other"
        if any(word in cleaned_input for word in ["paris", "vasco", "canada", "real madrid", "bahamas", "belgrade", "france", "europe", "australia", "london", "international", "club"]):
            return college_name.title(), "International", "Other"
        return college_name.title(), "Other", "Other"

    def get_college_info(player_name):
        match = [p for p in players.get_players() if p["full_name"].lower() == player_name.lower()]
        if not match:
            return "Unknown", "Other", "Other", None, "Unknown"
        player_id = match[0]["id"]
        time.sleep(0.6)
        info = commonplayerinfo.CommonPlayerInfo(player_id=player_id)
        df = info.get_data_frames()[0]
        school = df.iloc[0].get("SCHOOL", "Unknown")
        position = df.iloc[0].get("POSITION", "Unknown")
        school, school_type, conf = match_college_to_conf(school)
        return school, school_type, conf, player_id, position

    def get_all_game_ids(season):
        time.sleep(0.6)
        gamelog = leaguegamelog.LeagueGameLog(season=season, season_type_all_star="Regular Season")
        return gamelog.get_data_frames()[0]["GAME_ID"].unique().tolist()

    game_ids = get_all_game_ids(season)
    random.shuffle(game_ids)
    save_path = Path(save_path)
    save_path.mkdir(parents=True, exist_ok=True)

    for game_id in game_ids:
        try:
            time.sleep(0.6)
            boxscore = boxscoretraditionalv2.BoxScoreTraditionalV2(game_id=game_id)
            players_df = boxscore.get_data_frames()[0]
            starters = players_df[players_df["START_POSITION"].notnull()]
            starters = starters[starters["START_POSITION"] != ""]

            if len(starters["TEAM_ID"].unique()) < 2:
                continue

            summary = boxscoresummaryv2.BoxScoreSummaryV2(game_id=game_id)
            game_header = summary.get_data_frames()[0].iloc[0]
            home_team_id = game_header["HOME_TEAM_ID"]
            away_team_id = game_header["VISITOR_TEAM_ID"]

            home_abbr = players_df[players_df["TEAM_ID"] == home_team_id]["TEAM_ABBREVIATION"].iloc[0]
            away_abbr = players_df[players_df["TEAM_ID"] == away_team_id]["TEAM_ABBREVIATION"].iloc[0]
            home_score = int(players_df[players_df["TEAM_ID"] == home_team_id]["PTS"].sum())
            away_score = int(players_df[players_df["TEAM_ID"] == away_team_id]["PTS"].sum())

            matchup_str = f"{away_abbr} {away_score} - {home_score} {home_abbr}"

            team_lineups = []
            for team_id in [home_team_id, away_team_id]:
                team_starters = starters[starters["TEAM_ID"] == team_id].head(5)
                if len(team_starters) < 5:
                    continue

                team_abbr = team_starters["TEAM_ABBREVIATION"].iloc[0]
                opp_id = away_team_id if team_id == home_team_id else home_team_id
                opp_abbr = players_df[players_df["TEAM_ID"] == opp_id]["TEAM_ABBREVIATION"].iloc[0]

                quiz_data = {
                    "season": season,
                    "game_id": game_id,
                    "team_abbr": team_abbr,
                    "opponent_abbr": opp_abbr,
                    "matchup": matchup_str,
                    "players": []
                }

                team_players = players_df[players_df["TEAM_ID"] == team_id]
                team_total_pts = team_players["PTS"].sum()
                team_total_ast = team_players["AST"].sum()
                team_total_reb = team_players["REB"].sum()
                team_total_def = team_players["STL"].sum() + team_players["BLK"].sum()

                for _, row in team_starters.iterrows():
                    name = row["PLAYER_NAME"]
                    school, school_type, conf, player_id, position = get_college_info(name)

                    pts = row.get("PTS", 0)
                    ast = row.get("AST", 0)
                    reb = row.get("REB", 0)
                    stl = row.get("STL", 0)
                    blk = row.get("BLK", 0)
                    defense = stl + blk

                    contribution = {
                        "points_pct": round(pts / team_total_pts, 3) if team_total_pts else 0,
                        "assists_pct": round(ast / team_total_ast, 3) if team_total_ast else 0,
                        "rebounds_pct": round(reb / team_total_reb, 3) if team_total_reb else 0,
                        "defense_pct": round(defense / team_total_def, 3) if team_total_def else 0
                    }

                    quiz_data["players"].append({
                        "name": name,
                        "school": school,
                        "school_type": school_type,
                        "conference": conf,
                        "player_id": player_id,
                        "position": position,
                        "game_stats": {
                            "pts": pts,
                            "ast": ast,
                            "reb": reb,
                            "stl": stl,
                            "blk": blk
                        },
                        "game_contribution_pct": contribution
                    })

                team_lineups.append(quiz_data)

            if team_lineups:
                selected = random.choice(team_lineups)
                output = save_path / f"{selected['game_id']}_{selected['team_abbr']}.json"
                with open(output, "w", encoding="utf-8") as f:
                    json.dump(selected, f, indent=2, ensure_ascii=False)
                print(f"Saved quiz to {output}")
                return str(output)

        except Exception as e:
            print(f"Skipping game {game_id} due to error: {e}")
            continue

if __name__ == "__main__":
    path = generate_and_save_quiz(season="2021-22")
    print(f"Quiz saved to: {path}")

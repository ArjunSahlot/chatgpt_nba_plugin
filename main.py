import json
from nba_api.stats.static import players, teams
from nba_api.stats.endpoints import commonplayerinfo, playercareerstats
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.get("/")
async def home():
    html_content = """
    <!DOCTYPE html>
    <html>
        <head>
            <title>NBA API ChatGPT Plugin</title>
        </head>
        <body>
            <h1>NBA API ChatGPT Plugin</h1>
            <p>Created by <a href="https://github.com/ArjunSahlot">Arjun Sahlot</a></p>
            <p>Source code available on <a href="https://github.com/ArjunSahlot/chatgpt-nba-plugin">GitHub</a></p>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.get("/icon.jpg")
async def get_icon():
    print("icon")
    return FileResponse("icon.jpg", media_type="image/jpeg")


@app.get("/legal.md")
async def get_legal():
    print("legal")
    return FileResponse("legal.md", media_type="text/markdown")


@app.get("/.well-known/ai-plugin.json")
async def plugin_manifest():
    print("manifest")
    with open("ai-plugin.json") as f:
        return json.load(f)


@app.get("/player/{player_name}")
async def player_info(player_name: str):
    """
    Given a player name, this will return some common info about the player.
    nba_api.stats.endpoints.commonplayerinfo.CommonPlayerInfo is used to get the data.
    """
    print("player")
    player_id = players.find_players_by_full_name(player_name)[0]["id"]
    common_info = commonplayerinfo.CommonPlayerInfo(player_id=player_id).get_dict()
    data = {"info": {}}
    for i in range(len(common_info["resultSets"][0]["headers"])):
        data["info"][common_info["resultSets"][0]["headers"][i]] = common_info["resultSets"][0]["rowSet"][0][i]

    season_stats = common_info["resultSets"][1]["rowSet"][0][2]
    data[f"stats_during_{season_stats}"] = {}
    for i, category in enumerate(("PTS", "AST", "REB")):
        data[f"stats_during_{season_stats}"][category] = common_info["resultSets"][1]["rowSet"][0][i+3]

    return data


@app.get("/player/{player_name}/career")
async def player_career(player_name: str):
    print("career")
    player_id = players.find_players_by_full_name(player_name)[0]["id"]
    career_df = playercareerstats.PlayerCareerStats(player_id=player_id).get_data_frames()[0]
    career_dict = career_df.to_dict()
    data = {"PLAYER_ID": player_id, "career": {}}
    season_list = list(career_dict["SEASON_ID"].values())
    for season in season_list:
        data["career"][season] = {}

    for key, stat in career_dict.items():
        if key in ("PLAYER_ID", "SEASON_ID", "LEAGUE_ID", "TEAM_ID"):
            continue
        for ind, val in stat.items():
            data["career"][season_list[ind]][key] = val

    return data


@app.get("/player/{player_name}/{season}")
async def player_specific(player_name: str, season: str):
    """
    Specific stats for a player in a specific season.
    Season must be in the format: "YYYY-YY", ex: 2022-23
    """
    print("specific")
    if len(season) == 9:
        season = season[0:5] + season[7:9]
    player_id = players.find_players_by_full_name(player_name)[0]["id"]
    career_df = playercareerstats.PlayerCareerStats(player_id=player_id).get_data_frames()[0]
    season_stats = career_df[career_df["SEASON_ID"] == season]
    return {key: stat[list(stat.keys())[0]] for key, stat in season_stats.to_dict().items()}


# @app.get("/team/{team_name}")
# async def team_info(team_name: str):
#     team = teams.find_teams_by_full_name(team_name)[0]

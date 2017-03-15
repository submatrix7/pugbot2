import json
import requests

RAIDS = [('The Emerald Nightmare', 'EN'), ('Trial of Valor', 'TOV'), ('The Nighthold', 'NH')]
region_locale = {'us': ['us', 'en_US', 'en']}

def get_raid_progression(player_dictionary, raid):
    r = [x for x in player_dictionary["progression"]
    ["raids"] if x["name"] in raid][0]
    normal = 0
    heroic = 0
    mythic = 0
    for boss in r["bosses"]:
        if boss["normalKills"] > 0:
            normal += 1
        if boss["heroicKills"] > 0:
            heroic += 1
        if boss["mythicKills"] > 0:
            mythic += 1
    return {"normal": normal,
            "heroic": heroic,
            "mythic": mythic,
            "total_bosses": len(r["bosses"])}

def get_char(name, server, target_region, api_key):
    r = requests.get("https://%s.api.battle.net/wow/character/%s/%s?fields=items+progression+achievements&locale=%s&apikey=%s" % (
            region_locale[target_region][0], server, name, region_locale[target_region][1], api_key))

    if r.status_code != 200:
        raise Exception("Could Not Find Character (No 200 from API)")

    player_dict = json.loads(r.text)

    r = requests.get(
        "https://%s.api.battle.net/wow/data/character/classes?locale=%s&apikey=%s" % (
            region_locale[target_region][0], region_locale[target_region][1], api_key))
    if r.status_code != 200:
        raise Exception("Could Not Find Character Classes (No 200 From API)")
    class_dict = json.loads(r.text)
    class_dict = {c['id']: c['name'] for c in class_dict["classes"]}

    equipped_ivl = player_dict["items"]["averageItemLevelEquipped"]

    # Build raid progression
    raid_progress = {}
    for raid in RAIDS:
        raid_name = raid[0]
        raid_abrv = raid[1]
        raid_progress[raid_name] = {
            'abrv': raid_abrv,
            'progress': get_raid_progression(player_dict, raid_name)
        }
    armory_url = 'http://{}.battle.net/wow/{}/character/{}/{}/advanced'.format(
        region_locale[target_region][0], region_locale[target_region][2], server, name)
    return_string = ''
    return_string += "**%s** - **%s** - **%s %s**\n" % (
        name.title(), server.title(), player_dict['level'], class_dict[player_dict['class']])
    return_string += '<{}>\n'.format(armory_url)
    return_string += '```CSS\n'  # start Markdown

    # iLvL
    return_string += "Equipped Item TEST Level: %s\n" % equipped_ivl

    # Raid Progression
    for raid, data in raid_progress.items():
        progress = data['progress']
        return_string += '{abrv}: {normal}/{total} (N), {heroic}/{total} (H), {mythic}/{total} (M)\n'.format(
            abrv=data['abrv'],
            normal=progress['normal'],
            heroic=progress['heroic'],
            mythic=progress['mythic'],
            total=progress['total_bosses']
        )

async def pug(client, region, api_key, message):
    target_region = region
    try:
        i = str(message.content).split(' ')
        name = i[1]
        server = 'thrall'
        if len(i) == 4 and i[3].lower() in region_locale.keys():
            target_region = i[3].lower()
        character_info = get_char(name, server, target_region, api_key)
        await client.send_message(message.channel, character_info)
    except Exception as e:
        print(e)
        await client.send_message(message.channel, "(test)Error With Name or Server\n"
                                                   "Use: !pug <name> <server> <region>\n"
                                                   "Hyphenate Two Word Servers (Ex: Twisting-Nether)")

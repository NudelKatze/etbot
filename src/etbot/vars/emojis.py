import sys

from disnake.ext import commands

this = sys.modules[__name__]

yes_vote = None
no_vote = None
abstain_vote = None
recycle = '♻'
ear_with_hearing_aid = '🦻'
question = '❓'
one, two, three, four, five, six, seven, eight, nine, ten = '1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟'
options = [None, None, None, None, None, None, None, None, None, None]
bill_closed = None
void = None
withdrawn = None
imperial_authority = None
imperial_mandate = None


def initialize_testing_emojis(bot: commands.Bot):
    this.yes_vote = bot.get_emoji(867869297329176587)
    this.no_vote = bot.get_emoji(867869349041799198)
    this.abstain_vote = bot.get_emoji(867869367601070081)
    this.options = [one, two, three, four, five, six, seven, eight, nine, ten]
    this.bill_closed = bot.get_emoji(942907452360380457)
    this.void = bot.get_emoji(942907470207131658)
    this.withdrawn = bot.get_emoji(943070133193179167)
    this.imperial_authority = bot.get_emoji(943087345773707294)
    this.imperial_mandate = bot.get_emoji(947988924708560896)


def initialize_emojis(bot: commands.Bot):
    this.yes_vote = bot.get_emoji(698226023795261451)
    this.no_vote = bot.get_emoji(698226052899799130)
    this.abstain_vote = bot.get_emoji(698226077113516118)
    this.options = [one, two, three, four, five, six, seven, eight, nine, ten]
    this.bill_closed = bot.get_emoji(698468221929521222)
    this.void = bot.get_emoji(868451496595951656)
    this.withdrawn = bot.get_emoji(750073205389262908)
    this.imperial_authority = bot.get_emoji(503090066810339350)
    this.imperial_mandate = bot.get_emoji(503090308704370728)

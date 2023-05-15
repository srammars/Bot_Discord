import discord
from discord.ext import commands
from module1 import historique_commandes
from module2 import queue
from module3 import Tree
import json
import requests

intents = discord.Intents.all()
intents.members = True

bot = commands.Bot(command_prefix='$', intents=intents)

# Dictionnaire pour stocker les historiques des commandes de chaque utilisateur
historiques_utilisateurs = {}

# File d'attente pour les commandes Discord exécutées automatiquement
attente = queue("première commande")

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')

# Charger l'historique des commandes depuis le fichier JSON
try:
    with open("historique_commands.json", "r") as f:
        historique_commands = json.load(f)
except FileNotFoundError:
    historique_commands = historique_commandes()

# Enregistrer l'historique des commandes dans le fichier JSON
def enregistrer_historique():
    with open("historique_commands.json", "w") as f:
        json.dump(historique_commands, f)

# Ajouter une commande à l'historique des commandes d'un utilisateur
def ajouter_commande_utilisateur(ctx, user_id, commande):
    b = hacher_user_id(ctx.author.id)
    if hacher_user_id(user_id) in historique_commands:
        if hacher_user_id(user_id) == b:
            historique_commands[hacher_user_id(user_id)].append(commande)
    else:
        historique_commands[hacher_user_id(user_id)] = [commande]
    enregistrer_historique()

def hacher_user_id(user_id):
    # Choisissez une méthode de hachage appropriée
    hachage = 0
    for caractere in str(user_id):
        hachage += ord(caractere)
        hachage = (hachage * 31) % 2**32  # Utilisez un modulo pour limiter la taille du hachage si nécessaire
    return hachage


# Obtenir l'historique des commandes d'un utilisateur
def obtenir_historique_utilisateur(user_id):
    if user_id in historique_commands:
        return historique_commands[user_id]
    else:
        return []

# Exemple de commande pour enregistrer l'historique
@bot.command(name="hello" , help = "commande test")
async def hello(ctx):
    command = ctx.message.content 
    user_id = (ctx.author.id)
    ajouter_commande_utilisateur(ctx,user_id, command)
    await add_to_queue(command)
    await ctx.send(f'{ctx.author.mention} Commande ajoutée à la file d\'attente : **{command}**', embed=discord.Embed(description=f'Commande a etait exécute avec succes : {command}', color=discord.Color.orange()))
    global en_cours
    if not en_cours:
        en_cours = True
        await execute_command(command)

@bot.command(name="ping" , help = "commande test")
async def ping(ctx):

    c = hacher_user_id(ctx.author.id)

    command = ctx.message.content 
    user_id = ctx.author.id
    ajouter_commande_utilisateur(ctx,user_id,command)
    await add_to_queue(command)
    await ctx.send(f'{ctx.author.mention} Commande ajoutée à la file d\'attente : **{command}**', embed=discord.Embed(description=f'Commande a etait exécute avec succes : {command}', color=discord.Color.orange()))
    global en_cours
    if not en_cours:
        en_cours = True
        await execute_command(command)

# Exemple de commande pour afficher l'historique
@bot.command(name="history" , help ="Voir ton l'history")
async def history(ctx):
    c = hacher_user_id(ctx.author.id)
    if historique_commands:
        await ctx.send("Voici l'historique des commandes :")
        for user_id, commands in historique_commands.items():
            if user_id == c :
                await ctx.send(f"Utilisateur ID :{ctx.author.name} ")
                await ctx.send("Commandes :")
                for command in commands:
                    await ctx.send(command)
    else:
        await ctx.send("Pas d'historique de commandes")

@bot.command(name="history_all" ,help ="Voir toute l'history")
async def history_all(ctx):
    if historique_commands:
        await ctx.send("Voici l'historique des commandes :")
        for user_id, commands in historique_commands.items():
            await ctx.send(f"Utilisateur ID :{user_id} ")
            await ctx.send("Commandes :")
            for command in commands:
                await ctx.send(command)
    else:
        await ctx.send("Pas d'historique de commandes")

async def add_to_queue(command):
    if attente.first_node.data == "première commande":
        attente.first_node.data = command
    else:
        attente.append(command)

async def execute_command(ctx):
    global en_cours
    while True:
        command = attente.pop()
        if attente != command:
            break
        else:
            en_cours = True
            # créer un objet Context pour la commande "add"
            add_ctx = await bot.get_context(ctx.message)
            add_ctx.message.content = "$add " + command
            await bot.process_commands(add_ctx)
            await ctx.send(f'Exécution de la commande: {command}')
    en_cours = False

@bot.command(name="ban" , help = "bannir un utilisateur")
@commands.has_permissions(ban_members=True)  
async def ban(ctx, member : discord.Member, *, reason=None):
    await member.ban(reason=reason)
    await ctx.send(embed=discord.Embed(description=f"{member.mention} a été banni. Raison : {reason}"))

@bot.command(name="clear", help='Vider historique des commandes')
async def clear_history(ctx):
    historique_commands.clear()
    await ctx.send("Historique des commandes effacé.")

@bot.command(name="last", help="Afficher la dernière commande exécutée")
async def last_command(ctx):
    if ctx.author.name not in historique_commands or len(historique_commands[ctx.author.name]) == 0:
        await ctx.send("Pas d'historique de commandes pour cet utilisateur")
    else:
        last_command = historique_commands[ctx.author.name][-1]
        await ctx.send(f"Dernière commande exécutée par {ctx.author.name} : {last_command}")

@bot.command(name="purge", help='Supprimer des lignes')
async def clear_line(ctx, num_lines: int):
    await ctx.channel.purge(limit=num_lines + 1)
    await ctx.send(embed=discord.Embed(description=f"**{num_lines}** lignes de commande ont été effacées.", color=discord.Color.blue()))
    
@bot.command(name='role', help='Propose une liste de rôles existants à ajouter à un utilisateur.')
async def autocomplete_command(ctx, member: discord.Member):
    roles = ctx.guild.roles
    message = f"{ctx.author.mention}, quel rôle voulez-vous ajouter à {member.mention} ?\n"
    if ctx.author.name not in historique_commands:
        historique_commands[ctx.author.name] = []
    historique_commands[ctx.author.name].append('$role')
    for role in roles:
         message += f"```- {role.name}\n```"
    message += "**pour ajouter des roles faites $addrole**" # inclure la commande $addrole dans le message embed
    await ctx.send(embed=discord.Embed(description=message, color=discord.Color.green()))

    def check(msg):
        return msg.author == ctx.author and msg.channel == ctx.channel

    response = await bot.wait_for('message', check=check)
    if response.content == '$addrole': # vérifier si l'utilisateur a entré la commande $addrole
        await last_command(ctx, member) # appeler la fonction derniere_commande
        return

    role_name = response.content
    role = discord.utils.get(ctx.guild.roles, name=role_name)
    if role is None:
        return
    await member.add_roles(role)
    await ctx.send(f"Le rôle {role_name} a été ajouté à {member.mention}.")
    enregistrer_historique()

@bot.command(name="myhelp", help='Aide BotChat')
async def custom_help_command(ctx):
    """
    Affiche la liste des commandes disponibles et leur description.
    """
    commands = bot.commands
    message = f"{ctx.author.mention}, voici la liste des commandes disponibles :\n"
    for command in commands:
        if command.name != "help":
            message += f"```{command.name} : {command.help}```"
    await ctx.send(embed=discord.Embed(description=message, color=discord.Color.green()))


@bot.command(name='addrole', help='Ajoute un rôle à un utilisateur.')
async def add_role_command(ctx, member: discord.Member, role: discord.Role):
    attente.append('$addrole')
    await member.add_roles(role)
    embed = discord.Embed(title=f"Rôle ajouté !", description=f"Le rôle {role.mention} a été ajouté à {member.mention}.", color=0xFF5733)
    await ctx.send(embed=embed)
    if ctx.author.name not in historique_commands:
        historique_commands[ctx.author.name] = []
    historique_commands[ctx.author.name].append('$addrole')
    enregistrer_historique()
    attente.pop()

@bot.event
async def on_member_join(member):
    # Créer un salon de bienvenue pour l'utilisateur qui vient de rejoindre
    namemember = member.name
    channel = await member.guild.create_text_channel(f"bienvenue-{namemember}")

    # Modifier les autorisations du salon pour que seul l'utilisateur et le bot puissent voir le salon
    await channel.set_permissions(member, read_messages=True, send_messages=True)
    await channel.set_permissions(member.guild.default_role, read_messages=False)
    await channel.set_permissions(bot.user, read_messages=True)

    # Envoyer un message de bienvenue dans le salon de bienvenue
    message = f"Bienvenue dans le serveur de sram, {member.mention} !\n"
    message += "Réagissez avec les émoticônes correspondantes pour obtenir les rôles de votre choix :"
    message_embed = discord.Embed(description=message, color=discord.Color.green())
    
    emoji_list = ["1️⃣","2️⃣","3️⃣"] # Remplace ces émojis par ceux de ton choix
    role_list = ["Jeux", "Cours", "Stream"] # Remplace ces noms de rôles par ceux de ton choix

    for i in range(len(emoji_list)):
        message_embed.add_field(name=f"{   emoji_list[i]}  {role_list[i]} ", value="\u200b", inline=False)
    
    message_sent = await channel.send(embed=message_embed)
    for emoji in emoji_list:
        await message_sent.add_reaction(emoji)

    def check(reaction, user):
        return user == member and str(reaction.emoji) in emoji_list

    reaction, _ = await bot.wait_for('reaction_add', check=check)

    index = emoji_list.index(str(reaction.emoji))
    role = discord.utils.get(member.guild.roles, name=role_list[index])
    await member.add_roles(role)

    # Si l'utilisateur a réagi à plusieurs émoticônes
    while True:
        reaction, _ = await bot.wait_for('reaction_add', check=check)
        index = emoji_list.index(str(reaction.emoji))
        role = discord.utils.get(member.guild.roles, name=role_list[index])
        await member.add_roles(role)

        # Si toutes les émoticônes ont été sélectionnées
        selected_roles = [discord.utils.get(member.guild.roles, name=role_name) for role_name in role_list if discord.utils.get(member.guild.roles, name=role_name) in member.roles]
        if len(selected_roles) == len(role_list):
            continue

    await channel.send(f"{member.mention}, vous avez obtenu les rôles de votre choix !")

@bot.event
async def on_reaction_remove(reaction, user):
    member = reaction.message.guild.get_member(user.id)
    if member is None:
        return

    emoji_list = ["1️⃣", "2️⃣", "3️⃣"] # Remplace ces émojis par ceux de ton choix
    role_list = ["Jeux", "Cours", "Stream"] # Remplace ces noms de rôles par ceux de ton choix

    # Vérifie si la réaction est l'une des émoticônes des choix de rôle
    if str(reaction.emoji) in emoji_list:
        index = emoji_list.index(str(reaction.emoji))
        role = discord.utils.get(member.guild.roles, name=role_list[index])

        # Vérifie si l'utilisateur a le rôle attribué
        if role in member.roles:
            await member.remove_roles(role)
@bot.event
async def on_member_remove(member):
    namemember = member.name
    # Recherche le salon de bienvenue correspondant au membre qui a quitté le serveur
    channel_name = f"bienvenue-{namemember}"
    channel = discord.utils.get(member.guild.channels, name=channel_name)
    
    # Si le salon de bienvenue existe, le supprimer
    if channel:
        await channel.delete()
voice_channels = {}
user_channels = {}
user_last_channels = {}

@bot.command(name="cree" , help = "cree un channel vocal")
async def create_or_recreate_channel(ctx):
    command = ctx.message.content 
    # Récupération du serveur dans lequel la commande est tapée
    guild = ctx.guild
    # Récupération de la catégorie du canal où la commande est tapée
    category = ctx.channel.category
    if category is None:
        await ctx.send("Cette commande doit être exécutée dans une catégorie.")
        return
    # Récupération de l'utilisateur qui a tapé la commande
    user = ctx.author
    # Vérification si l'utilisateur a déjà un canal vocal
    if user.id in user_last_channels:
        # Récupération du dernier canal vocal créé par l'utilisateur
        last_channel = guild.get_channel(user_last_channels[user.id])
        # Vérification si le canal vocal existe toujours
        if last_channel is not None:
            await ctx.send(f"Vous avez déjà un canal vocal {last_channel.mention}.")
            return
        # Si le canal vocal n'existe plus, supprimer l'entrée du dictionnaire
        del user_last_channels[user.id]
    # Création d'un nouveau canal vocal avec le nom de l'utilisateur dans la catégorie détectée
    new_channel = await category.create_voice_channel(name=f"{user.name}'s Channel", user_limit=10)
    # Ajout de l'utilisateur au dictionnaire de canaux vocaux de l'utilisateur
    user_last_channels[user.id] = new_channel.id
    # Ajout du canal vocal au dictionnaire de canaux vocaux
    voice_channels[new_channel.id] = {"name": user.name, "users": [user.id]}
    historique_commands.setdefault(str(ctx.author.id), []).append(f"$cree : {new_channel.mention} a été créé avec une limite de 10 utilisateurs !")
    user_id = ctx.author.id
    ajouter_commande_utilisateur(ctx,user_id, command)
    await ctx.send(f"Votre nouveau canal vocal {new_channel.mention} a été créé avec une limite de 10 utilisateurs !")


@bot.command(name="invite" , help = "invitation channel vocal")
async def create_invite(ctx):
    # Récupération du canal vocal de l'utilisateur
    channel_id = user_last_channels.get(ctx.author.id)
    if channel_id is None:
        await ctx.send("Vous devez d'abord créer un salon vocal avec la commande $cree.")
        return
    voice_channel = ctx.guild.get_channel(channel_id)
    # Création d'une invitation pour le salon vocal de l'utilisateur
    invite = await voice_channel.create_invite()
    #await ctx.send(f"Invitation créée pour le salon vocal {voice_channel.mention} : {invite.url}")
    historique_commands.setdefault(str(ctx.author.id), []).append(f'$invite : {invite.url}')
    enregistrer_historique()

    await ctx.send(f"{invite.url}")



@bot.event
async def on_voice_state_update(member, before, after):
    if before.channel:
        guild_id = before.channel.guild.id
        if guild_id in voice_channels:
            if member.id in voice_channels[guild_id]["users"]:
                voice_channels[guild_id]["users"].remove(member.id)

        if len(before.channel.members) == 1 and before.channel.members[0].id != member.id:
            voice_channels[before.channel.id]["name"] = before.channel.members[0].name
            await before.channel.edit(name=f"{voice_channels[before.channel.id]['name']}'s Channel")

        if len(before.channel.members) == 0:
            if member.id in user_channels.values() and before.channel.id == user_channels[member.id]:
                del user_channels[member.id]
            del voice_channels[before.channel.id]
            await before.channel.delete()

@bot.command(name="voc_size" ,help = "channel vocal size")

async def set_voice_limit(ctx, limit: int):
    command = ctx.message.content 
    # Récupération du salon vocal dans lequel la commande est tapée
    voice_channel = ctx.author.voice.channel
    # Vérification si l'utilisateur est bien dans un salon vocal
    if voice_channel is None:
        await ctx.send("Vous devez être dans un salon vocal pour utiliser cette commande.")
        return
    # Vérification si l'utilisateur est le propriétaire du salon vocal
    if voice_channels[voice_channel.id]["name"] != ctx.author.name:
        await ctx.send("Vous devez être le propriétaire du salon vocal pour modifier sa limite d'utilisateurs.")
        return
    # Modification de la limite d'utilisateurs du salon vocal
    await voice_channel.edit(user_limit=limit)
    historique_commands[ctx.author.name].append(f'$modifmax : {limit}')
    user_id = ctx.author.id
    await ctx.send(f"La limite d'utilisateurs du salon vocal  a été modifiée à {limit}.")
    ajouter_commande_utilisateur(ctx,user_id, command)

@bot.command(name="deco" , help = "deconnecter un utiilisateur")
async def disconnect_user(ctx, member: discord.Member = None):
    # Récupération du salon vocal dans lequel la commande est tapée
    voice_channel = ctx.author.voice.channel
    # Vérification si l'utilisateur est bien dans un salon vocal
    if voice_channel is None:
        await ctx.send("Vous devez être dans un salon vocal pour utiliser cette commande.")
        return
    # Vérification si l'utilisateur est le propriétaire du salon vocal
    if voice_channels[voice_channel.id]["name"] != ctx.author.name:
        await ctx.send("Vous devez être le propriétaire du salon vocal pour utiliser cette commande.")
        return
    # Vérification si un utilisateur a été mentionné
    if member is None:
        await ctx.send("Vous devez mentionner un utilisateur à déconnecter.")
        return
    # Vérification si l'utilisateur mentionné est bien dans le salon vocal
    if member.voice is None or member.voice.channel != voice_channel:
        await ctx.send("Cet utilisateur n'est pas dans votre salon vocal.")
        return
    # Déconnexion de l'utilisateur du salon vocal
    await member.move_to(None)
    historique_commands[ctx.author.name].append(f'$deconnect : {member.mention} a été déconnecté de votre salon vocal.')
    enregistrer_historique()
    await ctx.send(f"{member.mention} a été déconnecté de votre salon vocal.")

async def create_invite(ctx, channel_id):
    # Récupération du salon vocal
    voice_channel = ctx.guild.get_channel(int(channel_id))
    if voice_channel is None:
        await ctx.send("Le salon vocal est introuvable.")
        return

    # Récupération de l'utilisateur qui a tapé la commande
    user = ctx.author

    # Vérification si l'utilisateur est dans le salon vocal
    if user not in voice_channel.members:
        await ctx.send("Vous devez être dans le salon vocal pour créer une invitation.")
        return

    # Création d'une invitation avec une durée de validité de 24 heures
    invite = await voice_channel.create_invite(max_age=86400)

    await ctx.send(f"Voici l'invitation pour le salon vocal **{voice_channel.name}** : {invite.url}")

@bot.event
async def on_message(message):
    # Vérifie si le message provient d'un utilisateur et non du bot lui-même
    if message.author == bot.user:
        return

    # Vérifie si le message est un signalement
    if message.content.startswith('$signaler'):
        # Récupère le channel de signalements
        channel_id = 1107470043920465970  # Remplacez par l'ID du channel de signalements
        channel = bot.get_channel(channel_id)

        if channel:
            # Supprime la commande !signaler du message
            signalement = message.content.replace('$signaler', '')

            # Envoie le signalement dans le channel spécifié
            await channel.send(f'Signalement de {message.author.mention}: {signalement}')
            
            await message.channel.send(f"{message.author.mention} Votre signalement a été enregistré.")
        else:
            await message.channel.send(f"Le channel de signalement n'a pas été trouvé.")

    await bot.process_commands(message)

#-----------------------------------------------------------------------------
tree = Tree("En quoi vous-avez besoin d'aide | signalement | role | ?")

tree.append("signalement", "Vous voulez signaler un | utilisateur | ?", "En quoi vous-avez besoin d'aide | signalement | role | ?")

tree.append("utilisateur", "le signalement ce fait via une commande faite | commande | pour plus de detaille", "Vous voulez signaler un | utilisateur | ?")
tree.append("commande", "faites : $signaler [utilisateur] [signalement] ", "le signalement ce fait via une commande faite | commande | pour plus de detaille")


tree.append("role", "vous voulez quoi comme roles  | stream | cours | jeux | ", "En quoi vous-avez besoin d'aide | signalement | role | ?")

tree.append("stream", "pour cela vous devez passer par la commande | $addrole |", "vous voulez quoi comme roles  | stream | cours | jeux | ")
tree.append("$addrole", "faite : $addrole [utilisateur] [role] ", "pour cela vous devez passer par la commande | $addrole |")

tree.append("cours", "pour cela vous devez passer par la commande | $addrole |", "vous voulez quoi comme roles  | stream | cours | jeux | ")
tree.append("$addrole", "faite : $addrole [utilisateur] [role] ", "pour cela vous devez passer par la commande | $addrole |")

tree.append("jeux", "pour cela vous devez passer par la commande | $addrole |", "vous voulez quoi comme roles  | stream | cours | jeux | ")
tree.append("$addrole", "faite : $addrole [utilisateur] [role] ", "pour cela vous devez passer par la commande | $addrole |")


questioning = False
@bot.command(name="tree" , help = "commencer la discution avec le bot")
async def helpp(ctx):
    global questioning, tree

    if questioning == False:
        questioning = True
        current_context = ctx
        current_question = tree.get_question()

        while current_question:
            if current_question == "faites : $signaler [utilisateur] [signalement] ":
                await current_context.send('faites : $signaler [utilisateur] [signalement] ')
                questioning = False
                return
            if current_question == "faite : $addrole [utilisateur] [role] ":
                await current_context.send('faite : $addrole [utilisateur] [role] ')
                questioning = False
                return

            question_message = await current_context.send(current_question)
            response = await bot.wait_for('message', check=lambda message: message.author == current_context.author)

            if response.content.lower() == '$stop':
                await current_context.send('Questionnement arrêté.')
                questioning = False
                return
            
            if not tree.choose(response):
                error_message = f'La réponse "{response.content}" n\'est pas valide. Veuillez réessayer.'
                await current_context.send(error_message)

            current_question = tree.get_question()

        await current_context.send('Traitement de la commande terminé.')
        questioning = False

@bot.command(name="reset" , help = "recommencer la discution avec le bot")
async def reset_questions(ctx):
    global questioning, tree

    if questioning:
        await ctx.send('Un questionnement est déjà en cours. Utilisez la commande $stop pour l\'arrêter avant de le réinitialiser.')
    else:
        tree.reset()  # Réinitialise l'arbre de questions
        questioning = True
        current_context = ctx
        current_question = tree.get_question()

        while current_question:
            if current_question == "faites : $signaler [utilisateur] [signalement] ":
                await current_context.send('faites : $signaler [utilisateur] [signalement] ')
                questioning = False
                return
            if current_question == "faite : $addrole [utilisateur] [role] ":
                await current_context.send('faite : $addrole [utilisateur] [role] ')
                questioning = False
                return

            question_message = await current_context.send(current_question)
            response = await bot.wait_for('message', check=lambda message: message.author == current_context.author)

            if response.content.lower() == '$stop':
                await current_context.send('Questionnement arrêté.')
                questioning = False
                return

            if not tree.choose(response):
                error_message = f'La réponse "{response.content}" n\'est pas valide. Veuillez réessayer.'
                await current_context.send(error_message)

            current_question = tree.get_question()

        await current_context.send('Traitement de la commande terminé.')
        questioning = False
@bot.command(name="joke",help = "rigolons un peu")
async def joke(ctx):
    joke = get_joke()
    await ctx.send(joke)

def get_joke():
    url = "https://v2.jokeapi.dev/joke/Any?lang=fr"  # L'URL de l'API JokeAPI

    response = requests.get(url)
    data = response.json()

    if data['type'] == 'single':
        joke = data['joke']
    else:
        joke = f"{data['setup']} {data['delivery']}"

    return joke

def run_bot(token):
    @bot.event
    async def on_ready():
        print('Bot is ready.')
    bot.run(token)

if __name__ == '__main__':
    token = 'MTA5Mzg4MTE1MzI1MDkzNDgwNw.G8goyi.Y02d_kyPFDS_JD01nFVGGIvBEwxJvb_LomKNG4'
    run_bot(token)

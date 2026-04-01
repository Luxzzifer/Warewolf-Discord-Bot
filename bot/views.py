# views.py
import discord
import random
import asyncio
from typing import List
from game_data import game, ROLES
from utils import get_alive_players, get_werewolves, is_moderator, check_winner, get_alignment, send_role_dm, generate_roles
from witch_views import WitchSaveView

# Kill View - Dropdown untuk memilih target
class KillView(discord.ui.View):
    def __init__(self, werewolf: discord.Member):
        super().__init__(timeout=60)
        self.werewolf = werewolf
        self.add_target_select()
    
    def add_target_select(self):
        alive_players = [p for p in get_alive_players() if p.id != self.werewolf.id]
        
        if not alive_players:
            return
        
        options = [
            discord.SelectOption(
                label=player.display_name[:100],
                value=str(player.id),
                description=f"Target untuk dibunuh"
            ) for player in alive_players
        ]
        
        select = discord.ui.Select(
            placeholder="🎯 Pilih target yang akan dibunuh",
            options=options,
            min_values=1,
            max_values=1
        )
        select.callback = self.select_target
        self.add_item(select)
    
    async def select_target(self, interaction: discord.Interaction):
        if interaction.user.id != self.werewolf.id:
            await interaction.response.send_message("❌ Ini bukan menu untuk Anda!", ephemeral=True)
            return
        
        target_id = int(interaction.data['values'][0])
        target = interaction.guild.get_member(target_id)
        
        if not target:
            await interaction.response.send_message("❌ Target tidak ditemukan!", ephemeral=True)
            return
        
        if target.id in game.dead_players:
            await interaction.response.send_message(f"❌ **{target.display_name}** sudah mati!", ephemeral=True)
            return
        
        if game.has_killed_this_night:
            await interaction.response.send_message("❌ Sudah ada Werewolf yang membunuh malam ini! Hanya 1 per malam.", ephemeral=True)
            return
        
        game.night_kills[self.werewolf.id] = target.id
        game.has_killed_this_night = True
        
        target_role = game.roles.get(target.id)
        
        if target_role == "tough_guy":
            game.tough_guy_hits[target.id] = game.tough_guy_hits.get(target.id, 0) + 1
            if game.tough_guy_hits[target.id] >= 2:
                game.dead_players.append(target.id)
                await interaction.response.send_message(f"✅ **{target.display_name}** berhasil dibunuh! (Tough Guy)", ephemeral=True)
            else:
                if target.id not in game.tough_guy_survived:
                    game.tough_guy_survived.append(target.id)
                await interaction.response.send_message(f"⚠️ **{target.display_name}** selamat! Tough Guy butuh 1 serangan lagi.", ephemeral=True)
        else:
            game.dead_players.append(target.id)
            await interaction.response.send_message(f"✅ **{target.display_name}** berhasil dibunuh!", ephemeral=True)
        
        moderator = interaction.guild.get_member(game.moderator_id)
        if moderator:
            embed = discord.Embed(
                title="🐺 PEMBUNUHAN",
                description=f"**Werewolf:** {self.werewolf.display_name}\n**Target:** {target.display_name}\n**Role:** {ROLES[target_role]['name'] if target_role else 'Unknown'}",
                color=discord.Color.dark_red()
            )
            await moderator.send(embed=embed)
        
        self.stop()
        await check_winner(interaction)

# Terawang View - Dropdown untuk memilih target
class TerawangView(discord.ui.View):
    def __init__(self, seer: discord.Member):
        super().__init__(timeout=60)
        self.seer = seer
        self.add_target_select()
    
    def add_target_select(self):
        alive_players = [p for p in get_alive_players() if p.id != self.seer.id]
        
        if not alive_players:
            return
        
        options = [
            discord.SelectOption(
                label=player.display_name[:100],
                value=str(player.id),
                description=f"Target untuk diterawang"
            ) for player in alive_players
        ]
        
        select = discord.ui.Select(
            placeholder="🔮 Pilih target yang akan diterawang",
            options=options,
            min_values=1,
            max_values=1
        )
        select.callback = self.select_target
        self.add_item(select)
    
    async def select_target(self, interaction: discord.Interaction):
        if interaction.user.id != self.seer.id:
            await interaction.response.send_message("❌ Ini bukan menu untuk Anda!", ephemeral=True)
            return
        
        target_id = int(interaction.data['values'][0])
        target = interaction.guild.get_member(target_id)
        
        if not target:
            await interaction.response.send_message("❌ Target tidak ditemukan!", ephemeral=True)
            return
        
        if game.seer_used.get(self.seer.id, False):
            await interaction.response.send_message("❌ Anda sudah menerawang malam ini!", ephemeral=True)
            return
        
        if target.id in game.dead_players:
            await interaction.response.send_message(f"❌ **{target.display_name}** sudah mati!", ephemeral=True)
            return
        
        target_role = game.roles.get(target.id)
        alignment = get_alignment(target_role)
        
        game.seer_used[self.seer.id] = True
        
        alignment_emoji = "😇" if alignment == "baik" else "👿"
        alignment_text = "**BAIK**" if alignment == "baik" else "**JAHAT**"
        
        embed = discord.Embed(
            title="🔮 HASIL TERAWANG",
            description=f"Anda menerawang **{target.display_name}**\n\n{alignment_emoji} Pemain ini adalah {alignment_text}!",
            color=discord.Color.purple()
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
        moderator = interaction.guild.get_member(game.moderator_id)
        if moderator:
            mod_embed = discord.Embed(
                title="🔮 SEER MENGAWANG",
                description=f"**Seer:** {self.seer.display_name}\n**Target:** {target.display_name}\n**Role:** {ROLES[target_role]['name']}\n**Alignment:** {alignment}",
                color=discord.Color.blue()
            )
            await moderator.send(embed=mod_embed)
        
        self.stop()

# Vote View
class VoteView(discord.ui.View):
    def __init__(self, players: List[discord.Member]):
        super().__init__(timeout=120)
        self.players = players
        self.add_vote_buttons()
    
    def add_vote_buttons(self):
        for player in self.players:
            if player.id not in game.dead_players:
                button = discord.ui.Button(
                    label=player.display_name[:80],
                    style=discord.ButtonStyle.secondary,
                    custom_id=f"vote_{player.id}"
                )
                button.callback = self.create_vote_callback(player)
                self.add_item(button)
    
    def create_vote_callback(self, target_player):
        async def vote_callback(interaction: discord.Interaction):
            voter_id = interaction.user.id
            
            if voter_id in game.dead_players:
                await interaction.response.send_message("❌ Anda sudah mati!", ephemeral=True)
                return
            
            if not any(p.id == voter_id for p in game.players):
                await interaction.response.send_message("❌ Anda tidak terdaftar!", ephemeral=True)
                return
            
            if voter_id in game.votes:
                await interaction.response.send_message("❌ Anda sudah voting!", ephemeral=True)
                return
            
            game.votes[voter_id] = target_player.id
            await interaction.response.send_message(f"✅ Anda memilih **{target_player.display_name}**", ephemeral=True)
            await self.update_vote_message(interaction)
            
        return vote_callback
    
    async def update_vote_message(self, interaction: discord.Interaction):
        if not game.vote_message:
            return
            
        total_alive = len(get_alive_players())
        voted_count = len(game.votes)
        
        vote_counts = {}
        for target_id in game.votes.values():
            vote_counts[target_id] = vote_counts.get(target_id, 0) + 1
        
        embed = discord.Embed(title="🗳️ VOTING WEREWOLF", color=discord.Color.blue())
        for player in get_alive_players():
            count = vote_counts.get(player.id, 0)
            bar = "█" * min(count, 10) + "░" * (10 - min(count, 10))
            embed.add_field(name=f"👤 {player.display_name}", value=f"`{bar}` {count} suara", inline=True)
        
        embed.set_footer(text=f"Sudah voting: {voted_count}/{total_alive} | Waktu tersisa: 120 detik")
        await game.vote_message.edit(embed=embed, view=self)
        
        if voted_count >= total_alive:
            await self.end_voting(interaction)
    
    async def end_voting(self, interaction: discord.Interaction):
        if game.vote_ended:
            return
        game.vote_ended = True
        
        vote_counts = {}
        for target_id in game.votes.values():
            vote_counts[target_id] = vote_counts.get(target_id, 0) + 1
        
        if not vote_counts:
            return
        
        max_votes = max(vote_counts.values())
        eliminated = [pid for pid, votes in vote_counts.items() if votes == max_votes]
        
        result_embed = discord.Embed(title="⚰️ HASIL VOTING", color=discord.Color.dark_red())
        
        if len(eliminated) == 1:
            eliminated_player = next((p for p in game.players if p.id == eliminated[0]), None)
            if eliminated_player:
                game.dead_players.append(eliminated_player.id)
                result_embed.description = f"**{eliminated_player.display_name}** telah dieksekusi!"
                result_embed.color = discord.Color.red()
                
                role = game.roles.get(eliminated_player.id)
                if role:
                    result_embed.add_field(name="Role yang dieksekusi", value=ROLES[role]['name'], inline=False)
                    
                    if role in ["warewolf", "laycan"]:
                        result_embed.add_field(name="🏆 KEMENANGAN!", value="Warga berhasil menemukan penjahat!", inline=False)
                        await game.vote_message.edit(embed=result_embed, view=None)
                        await interaction.channel.send(embed=result_embed)
                        from utils import reset_game
                        await reset_game()
                        return
        else:
            result_embed.description = "🔵 SERI! Tidak ada yang mencapai suara terbanyak!"
            result_embed.color = discord.Color.orange()
        
        await game.vote_message.edit(embed=result_embed, view=None)
        await interaction.channel.send(embed=result_embed)
        await check_winner(interaction)

# Select Moderator View
class SelectModeratorView(discord.ui.View):
    def __init__(self, members: List[discord.Member]):
        super().__init__(timeout=60)
        select = discord.ui.Select(
            placeholder="Pilih moderator untuk game ini",
            options=[
                discord.SelectOption(
                    label=member.display_name[:100],
                    value=str(member.id),
                    description=f"@{member.name}"
                ) for member in members[:25]
            ]
        )
        select.callback = self.select_moderator
        self.add_item(select)
    
    async def select_moderator(self, interaction: discord.Interaction):
        game.moderator_id = int(interaction.data['values'][0])
        moderator = interaction.guild.get_member(game.moderator_id)
        game.moderator_name = moderator.display_name
        
        embed = discord.Embed(
            title="✅ MODERATOR TERPILIH",
            description=f"**{moderator.display_name}** telah dipilih sebagai moderator!\n\nSekarang gunakan `/start` untuk memulai game!\n\n⚠️ **Minimal 3 player** untuk bermain",
            color=discord.Color.green()
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=False)
        self.stop()

# Start View
class StartView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        
    @discord.ui.button(label="👍 JOIN GAME", style=discord.ButtonStyle.success, emoji="👍")
    async def join_game(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not game.game_active:
            await interaction.response.send_message("❌ Game belum dimulai!", ephemeral=True)
            return
        
        if interaction.user in game.players:
            await interaction.response.send_message("❌ Anda sudah bergabung!", ephemeral=True)
            return
        
        game.players.append(interaction.user)
        
        embed = discord.Embed(
            title="🎮 GAME WEREWOLF",
            description=f"**Player:** {len(game.players)} orang",
            color=discord.Color.green()
        )
        player_list = "\n".join([f"👤 {p.mention}" for p in game.players])
        embed.add_field(name="📋 DAFTAR PLAYER", value=player_list, inline=False)
        embed.set_footer(text="Tekan tombol 👍 untuk bergabung! (Minimal 3 player)")
        
        await interaction.response.edit_message(embed=embed, view=self)

# Role Assign View
class RoleAssignView(discord.ui.View):
    def __init__(self, moderator_id: int):
        super().__init__(timeout=60)
        self.moderator_id = moderator_id
        
    @discord.ui.button(label="Assign Roles", style=discord.ButtonStyle.primary, emoji="🎭")
    async def assign_roles(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_moderator(interaction):
            await interaction.response.send_message("❌ Hanya moderator!", ephemeral=True)
            return
        
        if not game.game_active or not game.players:
            await interaction.response.send_message("❌ Game belum dimulai atau tidak ada player!", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="🎭 ASSIGN ROLE",
            description=f"Total player: **{len(game.players)}** orang\n\nPilih metode assign role:",
            color=discord.Color.purple()
        )
        
        view = RoleAutoAssignView(self.moderator_id, len(game.players))
        await interaction.response.send_message(embed=embed, view=view, ephemeral=False)
        self.stop()

# Role Auto Assign View
class RoleAutoAssignView(discord.ui.View):
    def __init__(self, moderator_id: int, player_count: int):
        super().__init__(timeout=120)
        self.moderator_id = moderator_id
        self.player_count = player_count
        
    @discord.ui.button(label="✅ Auto Assign", style=discord.ButtonStyle.success, emoji="🎲")
    async def auto_assign(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_moderator(interaction):
            await interaction.response.send_message("❌ Hanya moderator!", ephemeral=True)
            return
        
        roles_list = generate_roles(self.player_count)
        random.shuffle(roles_list)
        
        game.roles.clear()
        for i, player in enumerate(game.players):
            game.roles[player.id] = roles_list[i]
        
        game.seer_used.clear()
        
        success_count = 0
        failed_players = []
        
        for player in game.players:
            try:
                await send_role_dm(player, game.roles[player.id])
                success_count += 1
            except Exception as e:
                print(f"Gagal kirim DM ke {player.name}: {e}")
                failed_players.append(player.display_name)
        
        role_summary = {}
        for role in roles_list:
            role_summary[role] = role_summary.get(role, 0) + 1
        
        summary = "\n".join([f"• {ROLES[role]['name']}: {count} orang" for role, count in role_summary.items()])
        msg = f"✅ Role dikirim ke {success_count}/{len(game.players)} player!\n\n📋 **KOMPOSISI ROLE:**\n{summary}"
        
        if failed_players:
            msg += f"\n⚠️ Gagal mengirim ke: {', '.join(failed_players)}"
        
        await interaction.response.edit_message(content=msg, view=None)
        self.stop()
    
    @discord.ui.button(label="✏️ Manual Assign", style=discord.ButtonStyle.secondary, emoji="📝")
    async def manual_assign(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_moderator(interaction):
            await interaction.response.send_message("❌ Hanya moderator!", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="🎭 MANUAL ASSIGN",
            description=f"Total player: **{len(game.players)}** orang\n\nPilih role untuk setiap player dari dropdown.",
            color=discord.Color.purple()
        )
        
        role_list = "\n".join([f"• **{data['name']}** - {data['desc']}" for data in ROLES.values()])
        embed.add_field(name="📜 ROLE TERSEDIA", value=role_list, inline=False)
        
        view = RoleSelectView(self.moderator_id, len(game.players))
        await interaction.response.edit_message(embed=embed, view=view)
        self.stop()

# Role Select View
class RoleSelectView(discord.ui.View):
    def __init__(self, moderator_id: int, player_count: int):
        super().__init__(timeout=120)
        self.moderator_id = moderator_id
        self.player_count = player_count
        self.selected_roles = []
        self.current_index = 0
        self.add_role_selection()
    
    def add_role_selection(self):
        options = [
            discord.SelectOption(
                label=data['name'],
                value=key,
                description=data['desc'][:50],
                emoji=data['name'][:1]
            ) for key, data in ROLES.items()
        ]
        
        select = discord.ui.Select(
            placeholder=f"Pilih role untuk Player {self.current_index + 1} dari {self.player_count}",
            options=options,
            min_values=1,
            max_values=1
        )
        select.callback = self.select_role
        self.add_item(select)
    
    async def select_role(self, interaction: discord.Interaction):
        if not is_moderator(interaction):
            await interaction.response.send_message("❌ Hanya moderator!", ephemeral=True)
            return
        
        selected = interaction.data['values'][0]
        self.selected_roles.append(selected)
        self.current_index += 1
        self.clear_items()
        
        if self.current_index < self.player_count:
            self.add_role_selection()
            cancel = discord.ui.Button(label="❌ Batal", style=discord.ButtonStyle.danger)
            cancel.callback = self.cancel_selection
            self.add_item(cancel)
            
            await interaction.response.edit_message(
                content=f"✅ Role Player {self.current_index}: **{ROLES[selected]['name']}**\nPilih role untuk Player {self.current_index + 1}:",
                view=self
            )
        else:
            await interaction.response.edit_message(
                content=f"✅ Semua role terpilih!\n" + "\n".join([f"{i+1}. {ROLES[r]['name']}" for i, r in enumerate(self.selected_roles)]),
                view=None
            )
            
            shuffled_players = random.sample(game.players, len(game.players))
            game.roles.clear()
            for i, player in enumerate(shuffled_players):
                game.roles[player.id] = self.selected_roles[i]
            
            game.seer_used.clear()
            
            success = 0
            failed = []
            for player in game.players:
                try:
                    await send_role_dm(player, game.roles[player.id])
                    success += 1
                except:
                    failed.append(player.display_name)
            
            msg = f"✅ Role dikirim ke {success}/{len(game.players)} player!"
            if failed:
                msg += f"\n⚠️ Gagal: {', '.join(failed)}"
            
            await interaction.followup.send(msg, ephemeral=False)
            self.stop()
    
    async def cancel_selection(self, interaction: discord.Interaction):
        if not is_moderator(interaction):
            return
        await interaction.response.edit_message(content="❌ Pemilihan dibatalkan.", view=None)
        self.stop()
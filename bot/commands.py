# bot/commands.py
import discord
from discord.ext import commands
from discord import app_commands
import random
import asyncio
from pathlib import Path
from typing import Optional, List, Dict

from .game_data import game, ROLES
from .utils import (
    is_moderator, has_moderator, check_moderator_exists,
    get_alive_players, get_werewolves, check_game_active,
    get_alignment, generate_roles, send_role_dm, reset_game,
    check_winner, check_image_folder
)

commands_registered = False


def setup_commands(bot):
    global commands_registered
    
    if commands_registered:
        print("[WARNING] Commands already registered, skipping...")
        return
    
    # ==================== MODERATOR COMMANDS ====================
    
    @bot.tree.command(name="setmod", description="Pilih moderator game Werewolf")
    async def set_moderator(interaction: discord.Interaction):
        if not interaction.guild:
            await interaction.response.send_message("[ERROR] Command hanya bisa di server!", ephemeral=True)
            return
        
        if game.moderator_id is not None:
            game.moderator_id = None
            game.moderator_name = None
        
        members = [m for m in interaction.guild.members if not m.bot]
        if not members:
            await interaction.response.send_message("[ERROR] Tidak ada member!", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="[GAME] PILIH MODERATOR",
            description="Pilih moderator yang akan memimpin game Werewolf\n\n[INFO] Moderator akan memiliki akses ke semua command game",
            color=discord.Color.blue()
        )
        
        options = []
        for member in members[:25]:
            options.append(discord.SelectOption(label=member.display_name[:100], value=str(member.id)))
        
        select = discord.ui.Select(placeholder="Pilih moderator", options=options)
        
        async def select_callback(interaction: discord.Interaction):
            game.moderator_id = int(select.values[0])
            moderator = interaction.guild.get_member(game.moderator_id)
            game.moderator_name = moderator.display_name
            await interaction.response.send_message(f"[OK] Moderator: {moderator.display_name} terpilih!", ephemeral=False)
        
        select.callback = select_callback
        
        view = discord.ui.View()
        view.add_item(select)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=False)

    @bot.tree.command(name="start", description="Memulai game Werewolf")
    async def start_game(interaction: discord.Interaction):
        if not interaction.guild:
            await interaction.response.send_message("[ERROR] Command hanya bisa di server!", ephemeral=True)
            return
        
        if not check_moderator_exists(interaction):
            embed = discord.Embed(
                title="⚠️ BELUM ADA MODERATOR",
                description="❌ **Tidak dapat memulai game tanpa moderator!**\n\nSilakan gunakan `/setmod` terlebih dahulu.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        if not is_moderator(interaction):
            await interaction.response.send_message(f"[ERROR] Hanya moderator {game.moderator_name} yang bisa memulai game!", ephemeral=True)
            return
        
        if game.game_active:
            await interaction.response.send_message("[ERROR] Game sedang berlangsung! Gunakan /end", ephemeral=True)
            return
        
        game.game_active = True
        game.modal_channel = interaction.channel
        game.dead_players.clear()
        game.night_kills.clear()
        game.has_killed_this_night = False
        game.tough_guy_hits.clear()
        game.seer_used.clear()
        game.tough_guy_survived.clear()
        game.witch_saved = False
        game.witch_potion_save = None
        
        embed = discord.Embed(
            title="[GAME] GAME WEREWOLF DIMULAI",
            description=f"**Moderator:** {game.moderator_name}\n\nTekan tombol JOIN untuk bergabung!\n[WARNING] Minimal 3 player\n[WARNING] Hanya SATU Werewolf yang bisa membunuh per malam!\n[INFO] Witch memiliki ramuan penyelamat (1x)\n[INFO] Laycan adalah warga biasa yang terlihat JAHAT oleh Seer!",
            color=discord.Color.blue()
        )
        
        view = StartView()
        await interaction.response.send_message(embed=embed, view=view)
        
        await asyncio.sleep(45)
        
        if len(game.players) < 3:
            await interaction.followup.send(f"[ERROR] Player tidak cukup! Hanya {len(game.players)} player. Game dibatalkan.", ephemeral=False)
            await reset_game()
            return
        
        role_embed = discord.Embed(
            title="[GAME] ASSIGN ROLE",
            description=f"**Total player:** {len(game.players)} orang\n\nTekan tombol untuk assign role.",
            color=discord.Color.purple()
        )
        
        role_view = RoleAssignView(game.moderator_id)
        await interaction.followup.send(embed=role_embed, view=role_view)

    @bot.tree.command(name="night", description="[MODERATOR] Memulai fase malam")
    async def start_night_phase(interaction: discord.Interaction):
        if not interaction.guild:
            await interaction.response.send_message("[ERROR] Command hanya bisa di server!", ephemeral=True)
            return
        
        if not check_moderator_exists(interaction):
            embed = discord.Embed(
                title="⚠️ BELUM ADA MODERATOR",
                description="❌ **Game tidak dapat dimulai tanpa moderator!**",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        if not is_moderator(interaction):
            await interaction.response.send_message(f"[ERROR] Hanya moderator!", ephemeral=True)
            return
        
        if not game.game_active:
            await interaction.response.send_message("[ERROR] Game tidak aktif!", ephemeral=True)
            return
        
        game.night_kills.clear()
        game.night_phase = True
        game.has_killed_this_night = False
        game.seer_used.clear()
        game.tough_guy_survived.clear()
        
        werewolves = get_werewolves()
        seers = [p for p in get_alive_players() if game.roles.get(p.id) == "seer"]
        witches = [p for p in get_alive_players() if game.roles.get(p.id) == "witch"]
        
        if not werewolves:
            await interaction.response.send_message("[ERROR] Tidak ada Werewolf hidup!", ephemeral=True)
            return
        
        # Kirim DM ke Werewolf
        for werewolf in werewolves:
            try:
                embed = discord.Embed(
                    title="[NIGHT] FASE MALAM DIMULAI",
                    description="**Waktunya berburu!**\n\nGunakan /kill untuk membuka menu pilih target!\n\n[WARNING] Hanya SATU Werewolf yang bisa membunuh per malam!",
                    color=discord.Color.dark_purple()
                )
                await werewolf.send(embed=embed)
            except:
                pass
        
        # Kirim DM ke Seer
        for seer in seers:
            try:
                embed = discord.Embed(
                    title="[NIGHT] FASE MALAM DIMULAI",
                    description="Gunakan /terawang untuk menerawang!\n[WARNING] Hanya bisa digunakan SEKALI per malam!",
                    color=discord.Color.dark_purple()
                )
                await seer.send(embed=embed)
            except:
                pass
        
        # Kirim DM ke Witch
        for witch in witches:
            try:
                embed = discord.Embed(
                    title="[NIGHT] FASE MALAM DIMULAI",
                    description="Gunakan /heal @pemain untuk menyelamatkan korban!\n[WARNING] Hanya bisa digunakan SEKALI sepanjang game!\n[INFO] Cek status ramuan dengan /witch_status",
                    color=discord.Color.dark_purple()
                )
                await witch.send(embed=embed)
            except:
                pass
        
        msg = f"[OK] **FASE MALAM DIMULAI!**\n[DM] DM dikirim ke {len(werewolves)} Werewolf, {len(seers)} Seer, dan {len(witches)} Witch.\n[CMD] Werewolf: /kill\n[CMD] Seer: /terawang\n[CMD] Witch: /heal @pemain"
        await interaction.response.send_message(msg, ephemeral=False)

    @bot.tree.command(name="endnight", description="[MODERATOR] Mengakhiri fase malam")
    async def end_night_phase(interaction: discord.Interaction):
        if not interaction.guild:
            await interaction.response.send_message("[ERROR] Command hanya bisa di server!", ephemeral=True)
            return
        
        if not check_moderator_exists(interaction):
            embed = discord.Embed(
                title="⚠️ BELUM ADA MODERATOR",
                description="❌ **Game tidak dapat dimulai tanpa moderator!**",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        if not is_moderator(interaction):
            await interaction.response.send_message(f"[ERROR] Hanya moderator!", ephemeral=True)
            return
        
        if not game.game_active:
            await interaction.response.send_message("[ERROR] Game tidak aktif!", ephemeral=True)
            return
        
        if not game.night_phase:
            await interaction.response.send_message("[ERROR] Bukan fase malam!", ephemeral=True)
            return
        
        game.night_phase = False
        
        description_parts = []
        
        if game.night_kills:
            victims = []
            for target_id in game.night_kills.values():
                target = interaction.guild.get_member(target_id)
                if target:
                    victims.append({
                        "id": target_id,
                        "name": target.display_name
                    })
            
            if victims:
                victim = victims[0]
                if victim['id'] in game.dead_players:
                    description_parts.append(f"[DEATH] {victim['name']} meninggal dunia!")
                else:
                    description_parts.append(f"[SAVED] {victim['name']} diselamatkan oleh Witch!")
        
        if game.tough_guy_survived:
            for tg_id in game.tough_guy_survived:
                tg = interaction.guild.get_member(tg_id)
                if tg:
                    description_parts.append(f"[TOUGH] {tg.display_name} berhasil bertahan dari serangan Werewolf!")
        
        embed = discord.Embed(title="[NIGHT] RINGKASAN MALAM INI", color=discord.Color.dark_purple())
        
        if description_parts:
            embed.description = "\n".join(description_parts)
        else:
            embed.description = "Tidak ada kejadian malam ini."
        
        embed.set_footer(text="[SECURITY] Identitas Werewolf dirahasiakan!")
        await interaction.response.send_message(f"[OK] Fase malam berakhir!", embed=embed, ephemeral=False)
        
        # Detail untuk moderator
        moderator = interaction.guild.get_member(game.moderator_id)
        if moderator and game.night_kills:
            details = []
            for w_id, t_id in game.night_kills.items():
                werewolf = interaction.guild.get_member(w_id)
                target = interaction.guild.get_member(t_id)
                role = game.roles.get(t_id)
                saved = "[SAVED]" if t_id not in game.dead_players else "[DEAD]"
                if werewolf and target:
                    details.append(f"🐺 {werewolf.display_name} → 💀 {target.display_name} ({ROLES[role]['name'] if role else 'Unknown'}) {saved}")
            
            detail_embed = discord.Embed(title="📋 DETAIL PEMBUNUHAN", description="\n".join(details), color=discord.Color.blue())
            await moderator.send(embed=detail_embed)
        
        await check_winner(interaction)

    @bot.tree.command(name="vote", description="[MODERATOR] Memulai sesi voting")
    async def start_vote(interaction: discord.Interaction):
        if not interaction.guild:
            await interaction.response.send_message("[ERROR] Command hanya bisa di server!", ephemeral=True)
            return
        
        if not check_moderator_exists(interaction):
            embed = discord.Embed(
                title="⚠️ BELUM ADA MODERATOR",
                description="❌ **Game tidak dapat dimulai tanpa moderator!**",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        if not is_moderator(interaction):
            await interaction.response.send_message(f"[ERROR] Hanya moderator!", ephemeral=True)
            return
        
        if not game.game_active:
            await interaction.response.send_message("[ERROR] Game tidak aktif!", ephemeral=True)
            return
        
        if not game.roles:
            await interaction.response.send_message("[ERROR] Role belum di-assign!", ephemeral=True)
            return
        
        alive = get_alive_players()
        if len(alive) < 2:
            await interaction.response.send_message("[ERROR] Player hidup kurang dari 2!", ephemeral=True)
            return
        
        game.votes.clear()
        game.vote_ended = False
        
        embed = discord.Embed(title="[VOTE] VOTING WEREWOLF", description="Pilih siapa yang dicurigai!", color=discord.Color.blue())
        embed.add_field(name="[PLAYER] PLAYER HIDUP", value="\n".join([f"- {p.mention}" for p in alive]), inline=False)
        embed.set_footer(text="Waktu: 120 detik")
        
        view = VoteView(alive)
        game.vote_message = await interaction.response.send_message(embed=embed, view=view)
        game.vote_message = await interaction.original_response()

    @bot.tree.command(name="end", description="[MODERATOR] Mengakhiri game")
    async def end_game(interaction: discord.Interaction):
        if not interaction.guild:
            await interaction.response.send_message("[ERROR] Command hanya bisa di server!", ephemeral=True)
            return
        
        if not check_moderator_exists(interaction):
            embed = discord.Embed(
                title="⚠️ BELUM ADA MODERATOR",
                description="❌ **Tidak ada game yang berjalan tanpa moderator!**",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        if not is_moderator(interaction):
            await interaction.response.send_message(f"[ERROR] Hanya moderator!", ephemeral=True)
            return
        
        if not game.game_active:
            await interaction.response.send_message("[ERROR] Tidak ada game aktif!", ephemeral=True)
            return
        
        await reset_game()
        await interaction.response.send_message("[OK] Game diakhiri!", ephemeral=False)

    @bot.tree.command(name="status", description="[MODERATOR] Cek status game")
    async def game_status(interaction: discord.Interaction):
        if not interaction.guild:
            await interaction.response.send_message("[ERROR] Command hanya bisa di server!", ephemeral=True)
            return
        
        if not check_moderator_exists(interaction):
            embed = discord.Embed(
                title="⚠️ BELUM ADA MODERATOR",
                description="❌ **Tidak ada game yang berjalan tanpa moderator!**",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        if not is_moderator(interaction):
            await interaction.response.send_message(f"[ERROR] Hanya moderator!", ephemeral=True)
            return
        
        embed = discord.Embed(title="[STATUS] STATUS GAME", color=discord.Color.blue())
        embed.add_field(name="Moderator", value=game.moderator_name or "Belum", inline=True)
        embed.add_field(name="Active", value="YES" if game.game_active else "NO", inline=True)
        embed.add_field(name="Night Phase", value="YES" if game.night_phase else "NO", inline=True)
        embed.add_field(name="Total Player", value=str(len(game.players)), inline=True)
        embed.add_field(name="Dead", value=str(len(game.dead_players)), inline=True)
        embed.add_field(name="Alive", value=str(len(get_alive_players())), inline=True)
        embed.add_field(name="Witch Saved", value="YES" if game.witch_saved else "NO", inline=True)
        
        if game.witch_potion_save:
            saved_player = interaction.guild.get_member(game.witch_potion_save)
            if saved_player:
                embed.add_field(name="Saved Player", value=saved_player.display_name, inline=True)
        
        if game.players:
            player_list = "\n".join([f"{'[DEAD]' if p.id in game.dead_players else '[ALIVE]'} {p.display_name}" for p in game.players])
            embed.add_field(name="Player List", value=player_list[:1024], inline=False)
        
        if game.roles:
            role_list = "\n".join([f"{'[DEAD]' if p.id in game.dead_players else '[ALIVE]'} {p.display_name}: ||{game.roles[p.id].upper()}||" for p in game.players])
            embed.add_field(name="Roles (Hidden)", value=role_list[:1024], inline=False)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @bot.tree.command(name="guide", description="Panduan bermain Werewolf")
    async def game_guide(interaction: discord.Interaction):
        embed = discord.Embed(title="[GUIDE] PANDUAN WEREWOLF", description="Panduan lengkap bermain", color=discord.Color.gold())
        
        embed.add_field(
            name="CARA BERMAIN",
            value="1. /setmod - Pilih moderator (WAJIB!)\n2. /start - Mulai game\n3. Tekan JOIN - Bergabung (min 3)\n4. Assign role (Auto/Manual)\n5. /night - Fase malam (moderator)\n6. Werewolf: /kill - Pilih target\n7. Seer: /terawang - Pilih target\n8. Witch: /heal @pemain - Selamatkan korban\n9. /endnight - Akhiri malam\n10. /vote - Voting\n11. Player memilih target\n12. Eksekusi",
            inline=False
        )
        
        embed.add_field(
            name="ROLE & ALIGNMENT",
            value="**GOOD:** Seer, Tough Guy, Witch, Villager, Laycan\n**EVIL:** Werewolf\n\n" + 
                  "\n".join([f"**{data['name']}** - {data['desc']}" for data in ROLES.values()]),
            inline=False
        )
        
        embed.add_field(
            name="IMPORTANT RULES",
            value="- WAJIB pilih moderator dengan /setmod\n- Hanya 1 Werewolf yang bisa membunuh per malam!\n- Seer hanya bisa terawang 1x per malam\n- Witch: hanya 1 RAMUAN PENYELAMAT sepanjang game! Gunakan /heal @pemain\n- Laycan adalah warga biasa yang terlihat JAHAT oleh Seer\n- Tough Guy butuh 2 serangan\n- Voting 120 detik\n- Jika seri, tidak ada eksekusi",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=False)
    
    # ==================== PLAYER COMMANDS ====================
    
    @bot.tree.command(name="kill", description="[WEREWOLF] Membunuh satu pemain di malam hari")
    async def kill_player(interaction: discord.Interaction):
        if not check_moderator_exists(interaction):
            embed = discord.Embed(
                title="⚠️ BELUM ADA MODERATOR",
                description="❌ **Game tidak dapat dimulai tanpa moderator!**",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        if not check_game_active(interaction):
            await interaction.response.send_message("[ERROR] Game tidak aktif!", ephemeral=True)
            return
        
        if game.roles.get(interaction.user.id) != "warewolf":
            await interaction.response.send_message("[ERROR] Hanya Werewolf!", ephemeral=True)
            return
        
        if not game.night_phase:
            await interaction.response.send_message("[ERROR] Bukan fase malam! Gunakan /night dulu.", ephemeral=True)
            return
        
        if game.has_killed_this_night:
            await interaction.response.send_message("[ERROR] Sudah ada Werewolf yang membunuh malam ini!", ephemeral=True)
            return
        
        alive_players = [p for p in get_alive_players() if p.id != interaction.user.id]
        if not alive_players:
            await interaction.response.send_message("[ERROR] Tidak ada target!", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="[WEREWOLF] PILIH TARGET",
            description="Pilih target yang akan dibunuh malam ini!",
            color=discord.Color.dark_red()
        )
        
        view = KillView(interaction.user)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @bot.tree.command(name="terawang", description="[SEER ONLY] Melihat alignment Baik/Jahat seorang pemain")
    async def terawang(interaction: discord.Interaction):
        if not check_moderator_exists(interaction):
            embed = discord.Embed(
                title="⚠️ BELUM ADA MODERATOR",
                description="❌ **Game tidak dapat dimulai tanpa moderator!**",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        if game.roles.get(interaction.user.id) != "seer":
            await interaction.response.send_message("[ERROR] Hanya Seer!", ephemeral=True)
            return
        
        if not game.game_active:
            await interaction.response.send_message("[ERROR] Game tidak aktif!", ephemeral=True)
            return
        
        if not game.night_phase:
            await interaction.response.send_message("[ERROR] Hanya saat FASE MALAM! Gunakan /night dulu.", ephemeral=True)
            return
        
        if game.seer_used.get(interaction.user.id, False):
            await interaction.response.send_message("[ERROR] Sudah menerawang malam ini!", ephemeral=True)
            return
        
        alive_players = [p for p in get_alive_players() if p.id != interaction.user.id]
        if not alive_players:
            await interaction.response.send_message("[ERROR] Tidak ada target!", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="[SEER] PILIH TARGET",
            description="Pilih target yang akan diterawang malam ini!",
            color=discord.Color.purple()
        )
        
        view = TerawangView(interaction.user)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @bot.tree.command(name="heal", description="[WITCH] Menyelamatkan pemain yang mati")
    async def heal_player(interaction: discord.Interaction, player: discord.Member):
        """Command untuk Witch menyelamatkan pemain yang mati."""
        if not check_moderator_exists(interaction):
            embed = discord.Embed(
                title="⚠️ BELUM ADA MODERATOR",
                description="❌ **Game tidak dapat dimulai tanpa moderator!**",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        if not game.game_active:
            await interaction.response.send_message("[ERROR] Tidak ada game yang sedang berlangsung!", ephemeral=True)
            return
        
        if game.roles.get(interaction.user.id) != "witch":
            await interaction.response.send_message("[ERROR] Hanya Witch yang bisa menggunakan command ini!", ephemeral=True)
            return
        
        if game.witch_saved:
            await interaction.response.send_message("[ERROR] Anda sudah menggunakan ramuan penyelamat! Hanya bisa digunakan SEKALI.", ephemeral=True)
            return
        
        if not game.night_phase:
            await interaction.response.send_message("[ERROR] Anda hanya bisa menggunakan ramuan saat FASE MALAM! Gunakan /night dulu.", ephemeral=True)
            return
        
        if player.id not in game.dead_players:
            await interaction.response.send_message(f"[ERROR] {player.display_name} tidak dalam keadaan mati!", ephemeral=True)
            return
        
        # Selamatkan player
        game.dead_players.remove(player.id)
        game.witch_saved = True
        game.witch_potion_save = player.id
        
        embed = discord.Embed(
            title="🧙 RAMUAN PENYELAMAT",
            description=f"Anda telah menyelamatkan **{player.display_name}** dari kematian!",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=False)
        
        # Notifikasi ke player yang diselamatkan
        try:
            save_embed = discord.Embed(
                title="✨ ANDA DISELAMATKAN!",
                description=f"Witch **{interaction.user.display_name}** telah menyelamatkan Anda dari kematian!",
                color=discord.Color.green()
            )
            await player.send(embed=save_embed)
        except Exception:
            pass
        
        # Notifikasi ke moderator
        moderator = interaction.guild.get_member(game.moderator_id)
        if moderator:
            mod_embed = discord.Embed(
                title="🧙 WITCH MENYELAMATKAN",
                description=f"Witch **{interaction.user.display_name}** menyelamatkan **{player.display_name}**",
                color=discord.Color.green()
            )
            await moderator.send(embed=mod_embed)
        
        print(f"[WITCH] {interaction.user.display_name} menyelamatkan {player.display_name}")

    @bot.tree.command(name="witch_status", description="[WITCH] Cek status ramuan penyelamat")
    async def witch_status(interaction: discord.Interaction):
        """Command untuk Witch mengecek status ramuan penyelamat."""
        if not check_moderator_exists(interaction):
            embed = discord.Embed(
                title="⚠️ BELUM ADA MODERATOR",
                description="❌ **Game tidak dapat dimulai tanpa moderator!**",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        if not game.game_active:
            await interaction.response.send_message("[ERROR] Tidak ada game yang sedang berlangsung!", ephemeral=True)
            return
        
        if game.roles.get(interaction.user.id) != "witch":
            await interaction.response.send_message("[ERROR] Hanya Witch yang bisa menggunakan command ini!", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="🧙 STATUS RAMUAN WITCH",
            color=discord.Color.purple()
        )
        
        if game.witch_saved:
            embed.add_field(
                name="💚 RAMUAN PENYELAMAT",
                value="❌ **TELAH DIGUNAKAN**\nAnda sudah menggunakan ramuan penyelamat.",
                inline=False
            )
            if game.witch_potion_save:
                saved_player = interaction.guild.get_member(game.witch_potion_save)
                if saved_player:
                    embed.add_field(
                        name="📝 RIWAYAT",
                        value=f"Anda telah menyelamatkan **{saved_player.display_name}**",
                        inline=False
                    )
        else:
            embed.add_field(
                name="💚 RAMUAN PENYELAMAT",
                value="✅ **MASIH TERSEDIA**\nAnda dapat menyelamatkan **SATU** pemain yang mati.\n\n⚠️ Ramuan hanya bisa digunakan **SEKALI** dalam game!\n📝 Gunakan `/heal @pemain` untuk menyelamatkan.",
                inline=False
            )
        
        embed.set_footer(text="Pilih dengan bijak! Ramuan penyelamat hanya sekali pakai.")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    # ==================== VIEW CLASSES ====================
    
    class StartView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=60)
            
        @discord.ui.button(label="JOIN GAME", style=discord.ButtonStyle.success, emoji="👍")
        async def join_game(self, interaction: discord.Interaction, button: discord.ui.Button):
            if not game.game_active:
                await interaction.response.send_message("[ERROR] Game belum dimulai!", ephemeral=True)
                return
            
            if interaction.user in game.players:
                await interaction.response.send_message("[ERROR] Anda sudah bergabung!", ephemeral=True)
                return
            
            game.players.append(interaction.user)
            
            embed = discord.Embed(
                title="[GAME] GAME WEREWOLF",
                description=f"**Player:** {len(game.players)} orang",
                color=discord.Color.green()
            )
            player_list = "\n".join([f"- {p.mention}" for p in game.players])
            embed.add_field(name="Player List", value=player_list, inline=False)
            embed.set_footer(text="Tekan tombol JOIN untuk bergabung! (Minimal 3 player)")
            
            await interaction.response.edit_message(embed=embed, view=self)
    
    class RoleAssignView(discord.ui.View):
        def __init__(self, moderator_id: int):
            super().__init__(timeout=60)
            self.moderator_id = moderator_id
            
        @discord.ui.button(label="Assign Roles", style=discord.ButtonStyle.primary, emoji="🎭")
        async def assign_roles(self, interaction: discord.Interaction, button: discord.ui.Button):
            if interaction.user.id != self.moderator_id:
                await interaction.response.send_message("[ERROR] Hanya moderator!", ephemeral=True)
                return
            
            roles_list = generate_roles(len(game.players))
            random.shuffle(roles_list)
            
            game.roles.clear()
            for i, player in enumerate(game.players):
                game.roles[player.id] = roles_list[i]
            
            success_count = 0
            failed_players = []
            
            for player in game.players:
                try:
                    await send_role_dm(player, game.roles[player.id])
                    success_count += 1
                except Exception as e:
                    print(f"Failed to DM {player.name}: {e}")
                    failed_players.append(player.display_name)
            
            role_summary = {}
            for role in roles_list:
                role_summary[role] = role_summary.get(role, 0) + 1
            
            summary = "\n".join([f"- {ROLES[role]['name']}: {count} players" for role, count in role_summary.items()])
            msg = f"[OK] Role sent to {success_count}/{len(game.players)} players!\n\n**ROLE COMPOSITION:**\n{summary}"
            
            if failed_players:
                msg += f"\n[WARNING] Failed to send to: {', '.join(failed_players)}"
            
            await interaction.response.send_message(msg, ephemeral=False)
            self.stop()
    
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
                    description="Target untuk dibunuh"
                ) for player in alive_players
            ]
            
            select = discord.ui.Select(
                placeholder="[WEREWOLF] Pilih target yang akan dibunuh",
                options=options,
                min_values=1,
                max_values=1
            )
            select.callback = self.select_target
            self.add_item(select)
        
        async def select_target(self, interaction: discord.Interaction):
            if interaction.user.id != self.werewolf.id:
                await interaction.response.send_message("[ERROR] Ini bukan menu untuk Anda!", ephemeral=True)
                return
            
            target_id = int(interaction.data['values'][0])
            target = interaction.guild.get_member(target_id)
            
            if not target:
                await interaction.response.send_message("[ERROR] Target tidak ditemukan!", ephemeral=True)
                return
            
            if target.id in game.dead_players:
                await interaction.response.send_message(f"[ERROR] {target.display_name} sudah mati!", ephemeral=True)
                return
            
            if game.has_killed_this_night:
                await interaction.response.send_message("[ERROR] Sudah ada Werewolf yang membunuh malam ini!", ephemeral=True)
                return
            
            game.night_kills[self.werewolf.id] = target.id
            game.has_killed_this_night = True
            
            target_role = game.roles.get(target.id)
            
            if target_role == "tough_guy":
                game.tough_guy_hits[target.id] = game.tough_guy_hits.get(target.id, 0) + 1
                if game.tough_guy_hits[target.id] >= 2:
                    game.dead_players.append(target.id)
                    await interaction.response.send_message(f"[OK] {target.display_name} berhasil dibunuh! (Tough Guy)", ephemeral=True)
                else:
                    if target.id not in game.tough_guy_survived:
                        game.tough_guy_survived.append(target.id)
                    await interaction.response.send_message(f"[WARNING] {target.display_name} selamat! Tough Guy butuh 1 serangan lagi.", ephemeral=True)
            else:
                game.dead_players.append(target.id)
                await interaction.response.send_message(f"[OK] {target.display_name} berhasil dibunuh!", ephemeral=True)
            
            moderator = interaction.guild.get_member(game.moderator_id)
            if moderator:
                embed = discord.Embed(
                    title="[WEREWOLF] PEMBUNUHAN",
                    description=f"**Werewolf:** {self.werewolf.display_name}\n**Target:** {target.display_name}\n**Role:** {ROLES[target_role]['name'] if target_role else 'Unknown'}",
                    color=discord.Color.dark_red()
                )
                await moderator.send(embed=embed)
            
            self.stop()
            await check_winner(interaction)
    
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
                    description="Target untuk diterawang"
                ) for player in alive_players
            ]
            
            select = discord.ui.Select(
                placeholder="[SEER] Pilih target yang akan diterawang",
                options=options,
                min_values=1,
                max_values=1
            )
            select.callback = self.select_target
            self.add_item(select)
        
        async def select_target(self, interaction: discord.Interaction):
            if interaction.user.id != self.seer.id:
                await interaction.response.send_message("[ERROR] Ini bukan menu untuk Anda!", ephemeral=True)
                return
            
            target_id = int(interaction.data['values'][0])
            target = interaction.guild.get_member(target_id)
            
            if not target:
                await interaction.response.send_message("[ERROR] Target tidak ditemukan!", ephemeral=True)
                return
            
            if game.seer_used.get(self.seer.id, False):
                await interaction.response.send_message("[ERROR] Anda sudah menerawang malam ini!", ephemeral=True)
                return
            
            if target.id in game.dead_players:
                await interaction.response.send_message(f"[ERROR] {target.display_name} sudah mati!", ephemeral=True)
                return
            
            target_role = game.roles.get(target.id)
            alignment = get_alignment(target_role)
            
            game.seer_used[self.seer.id] = True
            
            alignment_text = "GOOD" if alignment == "baik" else "EVIL"
            alignment_color = discord.Color.green() if alignment == "baik" else discord.Color.red()
            
            embed = discord.Embed(
                title="[SEER] HASIL TERAWANG",
                description=f"Anda menerawang **{target.display_name}**\n\nPemain ini adalah {alignment_text}!",
                color=alignment_color
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
            moderator = interaction.guild.get_member(game.moderator_id)
            if moderator:
                mod_embed = discord.Embed(
                    title="[SEER] SEER MENGAWANG",
                    description=f"**Seer:** {self.seer.display_name}\n**Target:** {target.display_name}\n**Role:** {ROLES[target_role]['name']}\n**Alignment:** {alignment}",
                    color=discord.Color.blue()
                )
                await moderator.send(embed=mod_embed)
            
            self.stop()
    
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
                    await interaction.response.send_message("[ERROR] Anda sudah mati!", ephemeral=True)
                    return
                
                if not any(p.id == voter_id for p in game.players):
                    await interaction.response.send_message("[ERROR] Anda tidak terdaftar!", ephemeral=True)
                    return
                
                if voter_id in game.votes:
                    await interaction.response.send_message("[ERROR] Anda sudah voting!", ephemeral=True)
                    return
                
                game.votes[voter_id] = target_player.id
                await interaction.response.send_message(f"[OK] Anda memilih {target_player.display_name}", ephemeral=True)
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
            
            embed = discord.Embed(title="[VOTE] VOTING WEREWOLF", color=discord.Color.blue())
            for player in get_alive_players():
                count = vote_counts.get(player.id, 0)
                bar = "|" * min(count, 10) + "-" * (10 - min(count, 10))
                embed.add_field(name=f"{player.display_name}", value=f"`{bar}` {count} votes", inline=True)
            
            embed.set_footer(text=f"Voted: {voted_count}/{total_alive} | Time left: 120 seconds")
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
            
            result_embed = discord.Embed(title="[VOTE] HASIL VOTING", color=discord.Color.dark_red())
            
            if len(eliminated) == 1:
                eliminated_player = next((p for p in game.players if p.id == eliminated[0]), None)
                if eliminated_player:
                    game.dead_players.append(eliminated_player.id)
                    result_embed.description = f"{eliminated_player.display_name} telah dieksekusi!"
                    result_embed.color = discord.Color.red()
                    
                    role = game.roles.get(eliminated_player.id)
                    if role:
                        result_embed.add_field(name="Role yang dieksekusi", value=ROLES[role]['name'], inline=False)
                        
                        if role == "warewolf":
                            result_embed.add_field(name="[WIN] KEMENANGAN!", value="Warga berhasil menemukan Werewolf!", inline=False)
                            await game.vote_message.edit(embed=result_embed, view=None)
                            await interaction.channel.send(embed=result_embed)
                            await reset_game()
                            return
            else:
                result_embed.description = "[DRAW] SERI! Tidak ada yang mencapai suara terbanyak!"
                result_embed.color = discord.Color.orange()
            
            await game.vote_message.edit(embed=result_embed, view=None)
            await interaction.channel.send(embed=result_embed)
            await check_winner(interaction)
    
    commands_registered = True
    print("[OK] Commands registered successfully")
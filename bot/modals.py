# modals.py
import discord
import random
from pathlib import Path
from game_data import game, ROLES

# Path ke folder gambar
IMAGE_FOLDER = Path(__file__).parent / "Pic"

class RoleInputModal(discord.ui.Modal, title="Input Role untuk Game"):
    roles_input = discord.ui.TextInput(
        label="Role yang akan digunakan",
        placeholder="Contoh: warewolf,seer,laycan (pisahkan dengan koma)",
        style=discord.TextStyle.paragraph,
        required=True
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            role_list = [r.strip().lower() for r in self.roles_input.value.split(',')]
            
            valid_roles = []
            for role in role_list:
                if role in ROLES:
                    valid_roles.append(role)
                else:
                    # Perbaiki pesan error untuk role yang tidak valid
                    await interaction.response.send_message(
                        f"❌ Role '{role}' tidak valid! Role yang tersedia: warewolf, seer, tough_guy, witch, laycan", 
                        ephemeral=True
                    )
                    return
            
            if len(valid_roles) != len(game.players):
                await interaction.response.send_message(
                    f"❌ Jumlah role ({len(valid_roles)}) tidak sesuai dengan jumlah player ({len(game.players)})!\n"
                    f"💡 Contoh untuk {len(game.players)} player: {', '.join(['warewolf'] + ['laycan'] * (len(game.players)-1))}", 
                    ephemeral=True
                )
                return
            
            # Acak role untuk setiap player
            shuffled_roles = random.sample(valid_roles, len(valid_roles))
            
            # Assign role ke player
            game.roles.clear()
            for i, player in enumerate(game.players):
                game.roles[player.id] = shuffled_roles[i]
            
            success_count = 0
            failed_players = []
            
            for player in game.players:
                try:
                    role_key = game.roles[player.id]
                    role_data = ROLES[role_key]
                    
                    embed = discord.Embed(
                        title="🎭 ROLE ANDA",
                        description=f"Anda adalah **{role_data['name']}**",
                        color=discord.Color.green()
                    )
                    embed.add_field(name="⚔️ KEMAMPUAN", value=role_data['desc'], inline=False)
                    embed.set_footer(text="⚠️ JANGAN BERITAHU ROLE ANDA KE PEMAIN LAIN!")
                    
                    image_path = IMAGE_FOLDER / role_data['image']
                    
                    if image_path.exists():
                        file = discord.File(image_path, filename=role_data['image'])
                        embed.set_image(url=f"attachment://{role_data['image']}")
                        await player.send(file=file, embed=embed)
                    else:
                        await player.send(embed=embed)
                    
                    success_count += 1
                    
                except Exception as e:
                    print(f"Gagal kirim DM ke {player.name}: {e}")
                    failed_players.append(player.display_name)
            
            confirmation_msg = f"✅ Role telah diacak dan dikirim ke {success_count}/{len(game.players)} player via DM!"
            
            if failed_players:
                confirmation_msg += f"\n⚠️ Gagal mengirim DM ke: {', '.join(failed_players)}"
                confirmation_msg += "\nPastikan player mengizinkan DM dari member server!"
            
            await interaction.response.send_message(confirmation_msg, ephemeral=False)
            
            print("\n📋 HASIL ASSIGN ROLE:")
            for player in game.players:
                role_key = game.roles[player.id]
                print(f"  • {player.display_name}: {role_key.upper()}")
            
            # Tampilkan pesan untuk memulai voting
            vote_embed = discord.Embed(
                title="🗳️ VOTING DIMULAI",
                description=f"Moderator **{game.moderator_name}**, gunakan `/vote` untuk memulai sesi voting!\n\nPlayer yang tersisa: {len([p for p in game.players if p.id not in game.dead_players])} orang",
                color=discord.Color.gold()
            )
            await interaction.channel.send(embed=vote_embed)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error: {str(e)}", ephemeral=True)
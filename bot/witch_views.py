# bot/witch_views.py
import discord
from .game_data import game

class WitchSaveView(discord.ui.View):
    """View untuk Witch menyelamatkan pemain yang dibunuh"""
    
    def __init__(self, witch: discord.Member, victim_id: int, victim_name: str):
        super().__init__(timeout=30)
        self.witch = witch
        self.victim_id = victim_id
        self.victim_name = victim_name
        
    @discord.ui.button(label="💚 SELAMATKAN", style=discord.ButtonStyle.success, emoji="💚")
    async def save_victim(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Tombol untuk menyelamatkan korban"""
        if interaction.user.id != self.witch.id:
            await interaction.response.send_message("❌ Ini bukan menu untuk Anda!", ephemeral=True)
            return
        
        if game.witch_saved:
            await interaction.response.send_message("❌ Ramuan penyelamat sudah pernah digunakan!", ephemeral=True)
            return
        
        target = interaction.guild.get_member(self.victim_id)
        if not target:
            await interaction.response.send_message("❌ Target tidak ditemukan!", ephemeral=True)
            return
        
        # Selamatkan korban
        if self.victim_id in game.dead_players:
            game.dead_players.remove(self.victim_id)
            game.witch_saved = True
            game.witch_potion_save = self.victim_id
            
            embed = discord.Embed(
                title="🧙 RAMUAN PENYELAMAT",
                description=f"Anda telah menyelamatkan **{target.display_name}** dari kematian!",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
            # Notifikasi ke moderator
            moderator = interaction.guild.get_member(game.moderator_id)
            if moderator:
                mod_embed = discord.Embed(
                    title="🧙 WITCH MENYELAMATKAN",
                    description=f"Witch **{self.witch.display_name}** menyelamatkan **{target.display_name}**",
                    color=discord.Color.green()
                )
                await moderator.send(embed=mod_embed)
        else:
            await interaction.response.send_message("❌ Korban sudah diselamatkan atau tidak dalam bahaya!", ephemeral=True)
        
        self.stop()
    
    @discord.ui.button(label="💀 BIARKAN MATI", style=discord.ButtonStyle.danger, emoji="💀")
    async def let_die(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Tombol untuk membiarkan korban mati"""
        if interaction.user.id != self.witch.id:
            await interaction.response.send_message("❌ Ini bukan menu untuk Anda!", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="🧙 KEPUTUSAN",
            description=f"Anda membiarkan **{self.victim_name}** mati tanpa pertolongan.",
            color=discord.Color.dark_red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
        # Notifikasi ke moderator
        moderator = interaction.guild.get_member(game.moderator_id)
        if moderator:
            await moderator.send(f"🧙 Witch **{self.witch.display_name}** membiarkan {self.victim_name} mati.")
        
        self.stop()
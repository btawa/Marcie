import discord


# Button based replacement for DiscordUtils' AutoEmbedPaginator.  Unlike reaction paging this
# doesn't need the Manage Messages permission.  Only the user who ran the command can page.

class CardPaginator(discord.ui.View):
    def __init__(self, author, embeds, timeout=120):
        super().__init__(timeout=timeout)
        self.author = author
        self.embeds = embeds
        self.index = 0
        self.message = None
        self._update_buttons()

    def _update_buttons(self):
        self.previous.disabled = self.index == 0
        self.next.disabled = self.index == len(self.embeds) - 1
        self.counter.label = f"{self.index + 1}/{len(self.embeds)}"

    async def send(self, ctx):
        if len(self.embeds) == 1:
            self.message = await ctx.channel.send(embed=self.embeds[0])
            self.stop()
        else:
            self.message = await ctx.channel.send(embed=self.embeds[0], view=self)

    async def interaction_check(self, interaction):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message('Only the person who ran the command can page through these cards.',
                                                    ephemeral=True)
            return False
        return True

    async def _show(self, interaction, index):
        self.index = index
        self._update_buttons()
        await interaction.response.edit_message(embed=self.embeds[self.index], view=self)

    @discord.ui.button(emoji='◀', style=discord.ButtonStyle.secondary)
    async def previous(self, interaction, button):
        await self._show(interaction, self.index - 1)

    @discord.ui.button(label='1/1', style=discord.ButtonStyle.secondary, disabled=True)
    async def counter(self, interaction, button):
        pass

    @discord.ui.button(emoji='▶', style=discord.ButtonStyle.secondary)
    async def next(self, interaction, button):
        await self._show(interaction, self.index + 1)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True

        if self.message:
            try:
                await self.message.edit(view=self)
            except discord.HTTPException:
                pass

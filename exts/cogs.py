from discord import app_commands
from discord.ext import commands

def cog_context_menu(name: str):
    """Decorator to mark a method as a context menu for automatic registration."""
    def decorator(func):
        # Store metadata on the function for the Cog to find later
        func._is_context_menu = True
        func._context_menu_name = name
        return func
    return decorator

class CommandsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot
        self._registered_menus = []

    async def cog_load(self):
        """Automatically register all methods marked with @cog_context_menu."""
        for attr_name in dir(self):
            method = getattr(self, attr_name)
            if hasattr(method, "_is_context_menu"):
                # Instantiate and bind the context menu to this Cog instance
                menu = app_commands.ContextMenu(
                    name=method._context_menu_name,
                    callback=method
                )
                self.bot.tree.add_command(menu)
                self._registered_menus.append(menu)

    async def cog_unload(self):
        """Clean up the tree when the Cog is unloaded."""
        for menu in self._registered_menus:
            self.bot.tree.remove_command(menu.name, type=menu.type)


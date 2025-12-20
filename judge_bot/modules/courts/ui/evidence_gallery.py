from collections.abc import Sequence
import discord

class EvidenceMediaGallery(discord.ui.LayoutView):
    def __init__(self, content: str, evidence_files: Sequence[tuple[discord.File, str | None, str | None]]):
        super().__init__(timeout=None)
        


        # 1. Main Text Display
        self.add_item(discord.ui.TextDisplay(content))

        # 2. Filter images and other files
        images = [f for f, content_type, _ in evidence_files if content_type and content_type.startswith("image/")]
        others = [(f, content_type, url) for f, content_type, url in evidence_files if not content_type or not content_type.startswith("image/")]

        # 3. Safe Media Gallery (Max 10 items)
        if images:
            gallery_items = [
                discord.MediaGalleryItem(media=img) 
                for img in images[:10]  # Hard limit to 10
            ]
            self.add_item(discord.ui.MediaGallery(*gallery_items))

        # 4. Grouped File Attachments
        if others:
            # Group download links into one text component to save space
            links = "\n".join([f"[{f.filename}]({url})" for f, _, url in others])
            self.add_item(discord.ui.TextDisplay(f"**Attached Files:**\n{links}"))
            
            # Optional: Add individual File components (up to remaining row space)
            for file, _, _ in others[:3]: 
                self.add_item(discord.ui.File(media=file))

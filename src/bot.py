from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
import os
from pathlib import Path
from .converter import convert_img

load_dotenv()
IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".tif",
    ".tiff",
    ".svg",
    ".bmp",
    ".img",
    ".raw",
    ".heic",
    ".webp",
}


Token = os.getenv("Bot_Token")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to Image to PDF Bot!\n\n"
        "📸 Send me the images you want to convert.\n"
        "📄 When you're finished, send /convert and I'll create your PDF.\n\n"
        "🆕 Use /new if you want to discard the current images and start over."
    )

def remove_files(folder_name: Path, context):
    
    if folder_name.exists():
        for file in folder_name.iterdir():
            if file.is_file():
                file.unlink()

    # if you want to use os instead of Path
    ''' if os.path.exists(folder_name):
        for filename in os.listdir(folder_name):
            file_path = os.path.join(folder_name, filename)

            if os.path.isfile(file_path):
                os.remove(file_path) '''
    
    context.user_data['images'] = []

async def process_file(tel_file, img_count: int, update: Update, context, extension: str):

    if not extension in IMAGE_EXTENSIONS:
        await update.message.reply_text('That file format is unsupported, \nplease upload a supported one!')
        return

    file = await tel_file.get_file()
        
    print('image received')

    user_id = update.effective_user.id
    user_folder = Path('../downloads') / str(user_id)
    
    img_folder = user_folder / 'images'
        
    os.makedirs(img_folder, exist_ok=True)
    # img_folder.mkdir(parents=True,exist_ok=True) alternative option or the above
    
    image_number = img_count + 1
    
    file_path = f"{img_folder}/{image_number:02d}{extension}"

    await file.download_to_drive(file_path)
    
    context.user_data.setdefault('images', []).append(file_path)
    await update.message.reply_text(f'received your image and saved successfully \n{image_number}')
    
async def receive_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    img_count = len(context.user_data.get('images', []))

    if img_count >= 20:
        await update.message.reply_text(
            "⚠️ You can upload a maximum of 20 images per PDF."
        )
        return
    
    photo = update.message.photo[-1] # because the last file of the list is the one with highest resolution
    
    await process_file(photo, img_count, update, context, '.jpg')

async def receive_document(update,context):

    img_count = len(context.user_data.get('images', []))

    if img_count >= 20:
        await update.message.reply_text(
            "⚠️ You can upload a maximum of 20 images per PDF."
        )
        return
    
    image = update.message.document

    extension = Path(image.file_name).suffix.lower()
    if extension not in IMAGE_EXTENSIONS:
        await update.message.reply_text(
            "❌ Please send a valid image file."
        )
        return
    
    await process_file(image, img_count, update, context, extension)
    
async def run_conversion (update, context, img_folder, image_paths, output_path):
    try: 
        await convert_img (image_paths, output_path)

        await update.message.reply_document(
            document = output_path
        )
        await update.message.reply_text(
            'Images converted successully!\n\n Send /new to start new conversion'
        )
        remove_files(img_folder, context)
    except Exception as e:
        print("conversion errror", e)

        await update.message.reply_text(
            "❌ Something went wrong while converting your images.\n"
            "Your images have been kept. Please try again."
        )

    finally:
        context.user_data['converting'] = False

async def convert_command(update, context):
    print('this is convert command', flush=True)
    user_id = update.effective_user.id

    if context.user_data.get("converting", False):
        await update.message.reply_text(
            "⏳ Your PDF is already being converted. Please wait."
        )
        return
    

    user_folder = Path('../downloads') / str(user_id)
    
    img_folder = user_folder / 'images'
    image_paths = sorted([path for path in img_folder.iterdir() if path.is_file()])

    if not image_paths:
        await update.message.reply_text("You haven't uploaded any image")
        return
    
    context.user_data['converting'] = True

    output_path = user_folder / "converted.pdf"

    context.application.create_task(
        run_conversion(update, context, img_folder, image_paths, output_path)
    )

    await update.message.reply_text("🔄 Converting your images...")

    
    
   


async def new_conversion_process(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('converting', False):
        print('------------------')
        await update.message.reply_text('Please wait till conversion finishes.')
        return
        
    user_id = update.effective_user.id
    user_folder = Path('../downloads') / str(user_id)
    img_folder = user_folder / 'images'
        
    remove_files(img_folder, context)

    await update.message.reply_text('New Conversion started\nSend me your images')


def create_application():
    app = Application.builder().token(Token).build()

    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('new', new_conversion_process))
    app.add_handler(CommandHandler('convert', convert_command))

    app.add_handler(MessageHandler(filters.PHOTO, receive_image))
    app.add_handler(MessageHandler(filters.Document.ALL, receive_document))

    print ('Bot is running')

    return app


if __name__== '__main__':
    create_application()
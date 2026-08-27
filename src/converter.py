from playwright.async_api import async_playwright
from pathlib import Path
async def main():
    images = [
       r'downloads\6612246169\01.jpg',
       r'downloads\6612246169\01.jpg' 
    ]
    output = Path('downloads')/'converted.pdf'

    await convert_img(images, output)

async def convert_img(image_paths, output_path):
    
    async with async_playwright() as p:      
        browser = None
        
        try:
            browser  = await p.chromium.launch(
                    headless=True,
                    executable_path=r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
            )
            
            page = await browser.new_page()
            await page.goto('https://www.ilovepdf.com/jpg_to_pdf')         

            file_input = page.locator('input[type="file"]')     
            await file_input.set_input_files(image_paths)

            convert_button = page.locator("#processTask") # a button inside the page to convert the images
            await convert_button.wait_for()    # wait till the represented element is available, waits till js loads the element
            await convert_button.click() 
            
            download_button = page.locator("#pickfiles")  # a link inside the page to download the converted 
            await download_button.wait_for()

            async with page.expect_download() as down_inf:
                await download_button.click()

            downloaded = await down_inf.value
            await downloaded.save_as(output_path)
            
            print('pdf Downloaded')

        except Exception as e:
            print('Converson failed', e)
            raise

        finally:
            if browser:
                await browser.close()

        

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from lxml import html
import time
import csv

# Initialize the WebDriver
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

# URL of the property listings page
url = "https://www.cbre.co.uk/property-search/office-space/listings/results?aspects=isLetting"
links = []
properties = []


def save_html(html_page, filename):
    """ Save the rendered HTML to a file """
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(html_page)
    print(f"Rendered HTML saved to '{filename}'.")


def extract_property_data(property_link, house_no):
    """ Extract data from the property page """
    try:
        driver.get(property_link)
        WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located(
                (By.XPATH, '//div[contains(@class, "cbre_container")]'))
        )
        print("Property Page loaded and element is visible.")

        # Scroll the page to load lazy-loaded content
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(0.5)  # Wait for the content to load

        current_html = driver.execute_script("return document.documentElement.outerHTML;")

        # Save the HTML for debugging
        # save_html(current_html, f"{house_no}_debug.html")

        # Parse the page source
        webpage = html.fromstring(current_html)

        company = "CBRE"
        country = "UK"
        postcode = " ".join(webpage.xpath('//h1[@class="cbre_h1"]//div[@id="addressLine2"]/div/span/text()')[0].split(" ")[1:])
        state = webpage.xpath('//div[@id="addressLine2"]/div/span/text()')[0].split()[0]
        title = webpage.xpath('//div[@class="cbre_container"]//div[@id="addressLine1"]/div/span/text()')[0]
        address = title + state + postcode
        property_type_text = webpage.xpath(
            '//div[contains(@class, "cbre_container")]//div[contains(@class, "propertyDetailsStrapline")]//span/text()')
        property_type = property_type_text[0].split()[0] if property_type_text else None
        property_description = webpage.xpath('//span[@data-test="pdp-property-long-description"]/text()')[0]
        property_size = webpage.xpath('//div[contains(@class, "cbre_subh2")]/div//span/text()')[0]

        agent_details = webpage.xpath('//div[@class="contactGroup"]//div[@class="contact"]//text()')
        map_coordinates_text = webpage.xpath('//div[contains(@class, "map")]/@data-coordinates')
        property_map_coordinates = map_coordinates_text[0] if map_coordinates_text else None
        property_sale_price = webpage.xpath('//div[@class="cbre_h1 headerValue"]//span/text()')[0]
        property_amenities = webpage.xpath('//ul[contains(@class, "cbre_bulletList")]//li/text()') if webpage.xpath(
            '//ul[contains(@class, "cbre_bulletList")]//li/text()') else None

        property_sale_type = "For Rent" if "For Rent" in webpage.xpath(
                '//span[contains(text(), "For Rent") or contains(text(), "For Sale")]//text()')[0] else "For Sale"

        property_rent_texts = webpage.xpath('//div[contains(@class, "leasesBlock")]//div[@class="cbre_table"]//text()')
        property_rent_details = " ".join([text.strip() for text in property_rent_texts if text.strip()])

        images = webpage.xpath('//div[@class="sc-gIqMXP hFTJrU"][1]//img/@src')

        # Check if any images were found
        if images:
            # Prepend the base URL to each image URL if it's relative
            images = ["https://www.cbre.co.uk" + image if not image.startswith("http") else image for image in images]
        else:
            images = None  # Set images to None if no images were found

        # Extract data using XPath
        property_data_dict = {
            "company_name": company,
            "property_title": title,  # done
            "property_address": address,  # done
            "postcode": postcode,  # done
            "house_number": house_no,  # done
            "state": state,  # done
            "country": country,  # done
            "property_type": property_type,  # done
            "property_description": property_description,  # done
            "property_map_coordinates": property_map_coordinates,  # done
            "property_size": property_size,  # done
            "date_added": None,  # Add appropriate XPath if available
            "property_sale_price": property_sale_price,  # done
            "property_amenities": property_amenities,  # done
            "property_images": images,  # done
            "property_rent_details": property_rent_details,
            "property_link": property_link,  # done
            "agent_name": agent_details[0] if len(agent_details) > 0 else None,  # done
            "agent_name2": agent_details[2] if len(agent_details) > 2 else None,  # done
            "agent_telephone": agent_details[0] if len(agent_details) > 0 else None,  # done
            "agent_telephone2": agent_details[2] if len(agent_details) > 2 else None,  # done
            "agent_email": agent_details[1] if len(agent_details) > 1 else None,  # done
            "agent_email2": agent_details[3] if len(agent_details) > 3 else None,  # done
            "agent_address": address,  # done
            "property_sale_type": property_sale_type  # done
        }
        return property_data_dict

    except Exception as e:
        print(f"Failed to extract data from {property_link}: {e}")
        return None


def add_links(rendered_html):
    """ Extract property links from the rendered HTML """
    webpage = html.fromstring(rendered_html)
    all_properties = webpage.xpath('//div[contains(@class, "external-libraries-card-container")]')
    for single_property in all_properties:
        link = "https://www.cbre.co.uk" + single_property.xpath('.//span/a/@href')[0]
        links.append(link)


def load_page_and_collect_links():
    """ Load pages and collect links from all pages """
    try:
        while True:
            WebDriverWait(driver, 20).until(
                EC.visibility_of_element_located(
                    (By.XPATH, '//div[contains(@class, "external-libraries-card-container")]'))
            )
            print("Page loaded and element is visible.")

            current_html = driver.execute_script("return document.documentElement.outerHTML;")
            add_links(current_html)

            try:
                time.sleep(0.2)
                next_button = driver.find_element(By.XPATH,
                                                  '//li[contains(@class, "next")]//a[not(@aria-disabled="true")]')
                driver.execute_script("arguments[0].click();", next_button)

            except Exception:
                print("No more pages to navigate. Stopping.")
                break

    except Exception as e:
        print(f"Error Message: {e}")
        driver.quit()


# Open the page
driver.get(url)
load_page_and_collect_links()

# Extract data from each property link
for house_no, link in enumerate(links):
    print(f"Processing {house_no} {link}...")
    property_data = extract_property_data(link, house_no + 1)
    if property_data:
        properties.append(property_data)
    time.sleep(0.5)  # Wait a bit between requests to avoid overwhelming the server


# Save the extracted data to a CSV file
output_file = 'properties_data.csv'
with open(output_file, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.DictWriter(file, fieldnames=properties[0].keys())
    writer.writeheader()
    writer.writerows(properties)

print(f"Data has been saved to {output_file}")

# Close the browser
driver.quit()
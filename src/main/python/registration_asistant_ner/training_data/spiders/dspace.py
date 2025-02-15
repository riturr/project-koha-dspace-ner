import scrapy
import scrapy.http
import scrapy.http.request
from urllib.parse import urlparse

DSPACE_COMMUNITY_URLS = [
    'https://repositorio.umsa.bo/xmlui/handle/123456789/17064/recent-submissions', # Vicerrectorado
]

class DSpaceSpider(scrapy.Spider):
    name = 'dspace'
    
    def __init__(self, community_url, *args, **kwargs):
        super(DSpaceSpider, self).__init__(*args, **kwargs)
        self.start_urls = [community_url]
        if "custom_settings" in kwargs:
            self.custom_settings = kwargs['custom_settings']

    def parse_metadata(self, response, **kwargs):
        '''
        Parse the metadata XML file to extract download links for files attached to the record.
        '''
        community_url = kwargs.get('community_url', None)
        record_url = kwargs.get('record_url', None)
        metadata_url = response.url

        metadata_namespaces = {
            'mets': 'http://www.loc.gov/METS/',
            'xlink': 'http://www.w3.org/TR/xlink/',
            'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
            'dim': 'http://www.dspace.org/xmlns/dspace/dim',
        }
        file_url_xpath = '/mets:METS/mets:fileSec/mets:fileGrp[1]/mets:file/mets:FLocat/@xlink:href'
        file_url = response.xpath(file_url_xpath, namespaces=metadata_namespaces).get()

        file_url = urlparse(metadata_url).scheme + '://' + urlparse(metadata_url).netloc + file_url

        yield {
            'community_url': community_url,
            'record_url': record_url,
            'metadata_url': metadata_url,
            'file_url': file_url,
            'file_urls': [file_url, metadata_url], # This is required for the FilesPipeline to download the file (if pipeline is enabled)
        }

    def parse_record(self, response, **kwargs):
        '''
        Parse the individual record page to extract details about the record.

        # Record Metadata
        URL it is included as a comment in the HTML as '<!-- External Metadata URL: cocoon://metadata/handle/<some-id>/<some-another-id>/mets.xml-->'
        Final URL is then in the form 'https://repositorio.umsa.bo/metadata/handle/<some-id>/<some-another-id>/mets.xml'.
        '''
        community_url = kwargs.get('community_url', None)

        metadata_url = response.xpath('//*[@id="aspect_artifactbrowser_ItemViewer_div_item-view"]/comment()').get()
        metadata_url = metadata_url.replace('<!-- External Metadata URL: cocoon://', '').replace('-->', '')
        metadata_url = urlparse(response.url).scheme + '://' + urlparse(response.url).netloc + '/xmlui/' + metadata_url

        yield scrapy.Request(metadata_url, callback=self.parse_metadata, cb_kwargs={'community_url': community_url, 'record_url': response.url})

    def parse(self, response):
        '''
        Get the URL of each record in the community.
        It also follows the pagination links to get all the records.
        '''
        for record in response.css('div.artifact-description'):
            record_url = urlparse(response.url).scheme + '://' + urlparse(response.url).netloc + record.css('a::attr(href)').get()
            # Scrape the individual record page to get details about the record
            yield scrapy.Request(record_url, callback=self.parse_record, cb_kwargs={'community_url': response.url})

        next_page = response.css('a.next-page-link::attr(href)').get()
        if next_page is not None:
            yield response.follow(next_page, self.parse)

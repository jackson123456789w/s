import requests
import socket
from colorama import Fore, Style, init
import whois

# Initialize Colorama
init(autoreset=True)

class OSINTTool:
    def __init__(self):
        self.banner()

    def banner(self):
        print(Fore.CYAN + Style.BRIGHT + """
        ██████╗ ███████╗██╗███╗   ██╗████████╗
        ██╔══██╗██╔════╝██║████╗  ██║╚══██╔══╝
        ██████╔╝█████╗  ██║██╔██╗ ██║   ██║   
        ██╔═══╝ ██╔══╝  ██║██║╚██╗██║   ██║   
        ██║     ██║     ██║██║ ╚████║   ██║   
        ╚═╝     ╚═╝     ╚═╝╚═╝  ╚═══╝   ╚═╝   
        """ + Fore.YELLOW + Style.BRIGHT + "\nAdvanced OSINT Tool - For Ethical Use Only\n")

    def menu(self):
        print(Fore.GREEN + Style.BRIGHT + "[1] WHOIS Lookup")
        print(Fore.GREEN + Style.BRIGHT + "[2] DNS Records Lookup")
        print(Fore.GREEN + Style.BRIGHT + "[3] Social Media Username Search")
        print(Fore.GREEN + Style.BRIGHT + "[4] IP Geolocation")
        print(Fore.GREEN + Style.BRIGHT + "[5] Validate Email Address")
        print(Fore.GREEN + Style.BRIGHT + "[6] Exit")

        choice = input(Fore.CYAN + "\nChoose an option: ")
        return choice

    def whois_lookup(self, domain):
        try:
            print(Fore.YELLOW + f"\nPerforming WHOIS lookup for {domain}...\n")
            w = whois.whois(domain)
            for key, value in w.items():
                print(Fore.GREEN + f"{key}: {value}")
        except Exception as e:
            print(Fore.RED + f"Error: {e}")

    def dns_lookup(self, domain):
        try:
            print(Fore.YELLOW + f"\nFetching DNS records for {domain}...\n")
            ip = socket.gethostbyname(domain)
            print(Fore.GREEN + f"IP Address: {ip}")
        except Exception as e:
            print(Fore.RED + f"Error: {e}")

    def social_media_search(self, username):
        platforms = ['facebook', 'twitter', 'instagram', 'linkedin']
        print(Fore.YELLOW + f"\nSearching for {username} on social media platforms...\n")
        for platform in platforms:
            url = f"https://{platform}.com/{username}"
            print(Fore.GREEN + f"Checking {platform.capitalize()}: {url}")

    def ip_geolocation(self, ip):
        try:
            print(Fore.YELLOW + f"\nFetching geolocation for IP: {ip}...\n")
            response = requests.get(f"https://ipinfo.io/{ip}/json")
            data = response.json()
            for key, value in data.items():
                print(Fore.GREEN + f"{key}: {value}")
        except Exception as e:
            print(Fore.RED + f"Error: {e}")

    def validate_email(self, email):
        try:
            print(Fore.YELLOW + f"\nValidating email: {email}...\n")
            api_key = "eTZvJEHPmUdHdZ9CtFTk9rB5lzB02Pc4"  # Replace with your API key
            response = requests.get(f"https://api.apilayer.com/email_verification/check?email={email}", headers={"apikey": api_key})
            data = response.json()
            for key, value in data.items():
                print(Fore.GREEN + f"{key}: {value}")
        except Exception as e:
            print(Fore.RED + f"Error: {e}")

    def run(self):
        while True:
            choice = self.menu()
            if choice == '1':
                domain = input(Fore.CYAN + "Enter domain: ")
                self.whois_lookup(domain)
            elif choice == '2':
                domain = input(Fore.CYAN + "Enter domain: ")
                self.dns_lookup(domain)
            elif choice == '3':
                username = input(Fore.CYAN + "Enter username: ")
                self.social_media_search(username)
            elif choice == '4':
                ip = input(Fore.CYAN + "Enter IP address: ")
                self.ip_geolocation(ip)
            elif choice == '5':
                email = input(Fore.CYAN + "Enter email address: ")
                self.validate_email(email)
            elif choice == '6':
                print(Fore.CYAN + "Exiting... Goodbye!")
                break
            else:
                print(Fore.RED + "Invalid choice. Please try again.")

if __name__ == "__main__":
    tool = OSINTTool()
    tool.run()

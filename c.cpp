#ifndef KEY_WOW64_64KEY
#define KEY_WOW64_64KEY 0x0100
#endif

#include <windows.h>
#include <iostream>
#include <string>

std::string GetWindowsProductKey()
{
    HKEY hKey;
    const char* subkey = "SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion";
    const char* value = "DigitalProductId";
    BYTE digitalProductId[256];
    DWORD size = sizeof(digitalProductId);

    // Open registry key
    if (RegOpenKeyExA(HKEY_LOCAL_MACHINE, subkey, 0, KEY_READ | KEY_WOW64_64KEY, &hKey) != ERROR_SUCCESS)
        return "Failed to open registry key.";

    // Query value
    if (RegQueryValueExA(hKey, value, NULL, NULL, digitalProductId, &size) != ERROR_SUCCESS)
    {
        RegCloseKey(hKey);
        return "Failed to read product ID.";
    }

    RegCloseKey(hKey);

    // Decode product key
    const char* digits = "BCDFGHJKMPQRTVWXY2346789";
    const int keyOffset = 52;
    char decodedKey[25];
    BYTE key[15];

    for (int i = 0; i < 15; i++)
        key[i] = digitalProductId[keyOffset + i];

    for (int i = 24; i >= 0; i--)
    {
        int current = 0;
        for (int j = 14; j >= 0; j--)
        {
            current = current * 256 + key[j];
            key[j] = current / 24;
            current %= 24;
        }
        decodedKey[i] = digits[current];
    }

    // Format key with dashes
    std::string productKey;
    for (int i = 0; i < 25; i++)
    {
        productKey += decodedKey[i];
        if ((i + 1) % 5 == 0 && i != 24)
            productKey += "-";
    }

    return productKey;
}

int main()
{
    std::string productKey = GetWindowsProductKey();
    std::cout << "Windows Product Key: " << productKey << std::endl;
    return 0;
}

#include "Memory.hpp"

DWORD targetPid = 0;
NTSTATUS status = 0;

bool hijacking::enableSeDebugPrivilege() {
    HANDLE hToken;
    TOKEN_PRIVILEGES tp = { 1 };
    if(!OpenProcessToken(GetCurrentProcess(), TOKEN_ADJUST_PRIVILEGES, &hToken)) return false;
    LookupPrivilegeValue(NULL, "SeDebugPrivilege", &tp.Privileges[0].Luid);
    tp.Privileges[0].Attributes = SE_PRIVILEGE_ENABLED;
    AdjustTokenPrivileges(hToken, FALSE, &tp, sizeof(tp), NULL, NULL);
    CloseHandle(hToken);
    return GetLastError() == ERROR_SUCCESS;
}

int hijacking::findProcessWithHandle(ULONG accessMask, LPCSTR windowName, DWORD* processPIDBuffer, HANDLE* duplicatedHandleBuffer, USHORT* originalHandleValue){
    HWND hwnd = FindWindowA(nullptr, windowName);
    if(!hwnd) return 0;

    DWORD windowPid;
    GetWindowThreadProcessId(hwnd, &windowPid);

    if(!windowPid)
        return 0;

    HMODULE hNtdll = GetModuleHandleA("ntdll.dll");
    fn_NtQuerySystemInformation NtQuerySystemInformation = (fn_NtQuerySystemInformation)GetProcAddress(hNtdll, "NtQuerySystemInformation");
    fn_NtOpenProcess NtOpenProcess = (fn_NtOpenProcess)GetProcAddress(hNtdll, "NtOpenProcess");
    fn_NtClose NtClose = (fn_NtClose)GetProcAddress(hNtdll, "NtClose");

    BYTE buffer[1048576];
    status = NtQuerySystemInformation(0x10, buffer, sizeof(buffer), NULL);
    if(STATUS_SUCCESS != status)
        return 0;

    SYSTEM_HANDLE_INFORMATION* SystemHandleInformation = (SYSTEM_HANDLE_INFORMATION*)buffer;

    for(int i = 0; i < SystemHandleInformation->Count; i++) {
        if((SystemHandleInformation->Handles[i].GrantedAccess & accessMask) == accessMask) {
            HANDLE handle = NULL;
            
            CLIENT_ID cid = {};
            cid.UniqueProcess = (HANDLE)(ULONG_PTR)SystemHandleInformation->Handles[i].UniqueProcessId;
            cid.UniqueThread = NULL;

            OBJECT_ATTRIBUTES oa = {};
            InitializeObjectAttributes(&oa, NULL, 0, NULL, NULL);

            status = NtOpenProcess(&handle, PROCESS_ALL_ACCESS, &oa, &cid);
            if(STATUS_SUCCESS != status || handle == NULL) {
                continue; 
            }

            HANDLE duplicatedHandle = NULL;
            BOOL dupOk = DuplicateHandle(handle, 
                (HANDLE)(ULONG_PTR)SystemHandleInformation->Handles[i].HandleValue, 
                GetCurrentProcess(), 
                &duplicatedHandle, 
                0, 
                FALSE, 
                DUPLICATE_SAME_ACCESS
            );

            if(dupOk && duplicatedHandle) {
                if(GetProcessId(duplicatedHandle) == windowPid) {
                    if(duplicatedHandleBuffer)
                        *duplicatedHandleBuffer = duplicatedHandle;

                    if(processPIDBuffer)
                        *processPIDBuffer = SystemHandleInformation->Handles[i].UniqueProcessId;

                    if(originalHandleValue)
                        *originalHandleValue = SystemHandleInformation->Handles[i].HandleValue;
                        
                    targetPid = SystemHandleInformation->Handles[i].UniqueProcessId;
                    
                    NtClose(handle);
                    return 1;
                }
                CloseHandle(duplicatedHandle);
            }
            NtClose(handle);
        }
    }
    return 0;
} 
    
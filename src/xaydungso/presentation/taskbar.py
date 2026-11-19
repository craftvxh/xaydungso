"""Give the main window its own Windows taskbar identity (and so the app logo).

When the app runs on Microsoft Store Python, Windows groups the window under the
Python package and shows the Python icon; a process-wide AppUserModelID is
ignored there. A per-window AppUserModelID (PKEY_AppUserModel_ID) is honoured,
so the taskbar button shows the window icon instead. Best effort: failures are
logged and never stop the app.
"""

import ctypes
import logging
import uuid

APP_ID = "xaydungso"  # Same id the Windows notifications use.
_PROPERTY_FMTID = "9F4C2855-9F79-4B39-A8D0-E1D42DE1D5F3"  # PKEY_AppUserModel_*
_PID_APP_ID = 5
_IID_PROPERTY_STORE = "886D8EEB-8CF2-4446-8D02-CDBA1DBDCF99"
_VT_LPWSTR = 31

logger = logging.getLogger(__name__)


def set_taskbar_identity(window, app_id: str = APP_ID) -> bool:
    """Set the window's AppUserModelID before it is shown; True on success."""
    try:
        _set_window_app_id(int(window.winId()), app_id)
        return True
    except OSError as error:  # Includes failed HRESULTs raised below.
        logger.warning("Could not set taskbar identity: %s", error)
        return False


def _set_window_app_id(hwnd: int, app_id: str) -> None:
    from ctypes import wintypes

    class GUID(ctypes.Structure):
        _fields_ = [
            ("Data1", wintypes.DWORD),
            ("Data2", wintypes.WORD),
            ("Data3", wintypes.WORD),
            ("Data4", ctypes.c_ubyte * 8),
        ]

    class PROPERTYKEY(ctypes.Structure):
        _fields_ = [("fmtid", GUID), ("pid", wintypes.DWORD)]

    class PROPVARIANT(ctypes.Structure):
        _fields_ = [
            ("vt", ctypes.c_ushort),
            ("reserved", ctypes.c_ushort * 3),
            ("value", ctypes.c_wchar_p),
            ("padding", ctypes.c_void_p),
        ]

    def guid(text):
        value = uuid.UUID(text)
        return GUID(
            value.time_low,
            value.time_mid,
            value.time_hi_version,
            (ctypes.c_ubyte * 8)(*value.bytes[8:]),
        )

    def check(result, action):
        if result < 0:
            raise OSError(f"{action} failed (HRESULT {result & 0xFFFFFFFF:#010x})")

    store = ctypes.c_void_p()
    iid = guid(_IID_PROPERTY_STORE)
    check(
        ctypes.windll.shell32.SHGetPropertyStoreForWindow(
            wintypes.HWND(hwnd), ctypes.byref(iid), ctypes.byref(store)
        ),
        "SHGetPropertyStoreForWindow",
    )
    # IPropertyStore vtable: IUnknown (0-2), GetCount, GetAt, GetValue, SetValue (6), Commit (7).
    table = ctypes.cast(
        ctypes.cast(store, ctypes.POINTER(ctypes.c_void_p))[0],
        ctypes.POINTER(ctypes.c_void_p),
    )
    method = ctypes.WINFUNCTYPE
    release = method(ctypes.c_ulong, ctypes.c_void_p)(table[2])
    set_value = method(
        ctypes.c_long,
        ctypes.c_void_p,
        ctypes.POINTER(PROPERTYKEY),
        ctypes.POINTER(PROPVARIANT),
    )(table[6])
    commit = method(ctypes.c_long, ctypes.c_void_p)(table[7])
    try:
        key = PROPERTYKEY(guid(_PROPERTY_FMTID), _PID_APP_ID)
        value = PROPVARIANT(_VT_LPWSTR, (ctypes.c_ushort * 3)(), app_id, None)
        check(set_value(store, ctypes.byref(key), ctypes.byref(value)), "SetValue")
        check(commit(store), "Commit")
    finally:
        release(store)

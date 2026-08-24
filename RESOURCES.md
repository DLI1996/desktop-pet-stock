# desktop-pet-stock Architecture Resources

## Knowledge

- [Qt for Python: Threads and QObjects](https://doc.qt.io/qtforpython-6/overviews/qtdoc-threads-qobject.html)
  Primary documentation for queued cross-thread signal delivery. Use when changing asynchronous quote fetching or UI updates.
- [Python: `urllib.request`](https://docs.python.org/3/library/urllib.request.html)
  Standard-library HTTP client documentation. Use when reviewing provider requests, TLS behavior, headers, and timeouts.
- [Python: `subprocess`](https://docs.python.org/3/library/subprocess.html)
  Primary documentation for child-process execution and security considerations. Use when reviewing automatic WPS/file launching or the bridge command.
- [Python: `webbrowser`](https://docs.python.org/3/library/webbrowser.html)
  Primary documentation for browser-launch behavior. Use when evaluating the automatic Douyin action.
- [Shanghai Stock Exchange: Trading Schedule](https://english.sse.com.cn/start/trading/schedule/)
  Official trading-session reference. Use to verify Shanghai market-hour and holiday assumptions.
- [Shenzhen Stock Exchange: Trading Overview](https://www.szse.cn/English/services/trading/tradOverview/index.html)
  Official trading-hours and auction reference. Use to verify Shenzhen session semantics.

## Wisdom (Communities)

- [Qt Forum](https://forum.qt.io/)
  Practitioner community for PySide/Qt threading and desktop lifecycle questions after reproducing a concrete issue.

## Gaps

- The Sina quote endpoint used by this project has no authoritative API contract recorded in the repository.
- No official source is yet selected for any exchange outside mainland China.

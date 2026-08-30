# Market Desktop Pet

The desktop pet reacts to one selected market instrument and lets the user choose that instrument from a market-specific catalog.

## Language

**Watched instrument**:
The specific index or stock whose quote drives the pet's card and market reaction.
_Avoid_: Metric, market, preset

**Instrument catalog**:
The list of watched instruments in the China market view.
_Avoid_: Index presets, metrics menu

**Market view**:
The China or US collection currently shown in the market panel. Each app session starts in the US view; changing the view does not itself select a watched instrument.
_Avoid_: Submenu, market mode, data mode

**Market switch**:
The paired `中国 / 美国` control that chooses the market view shown in the market panel.
_Avoid_: Instrument selector, persistent market mode

**Market panel**:
The compact surface shown beside the pet after hover. It replaces the original mini quote card and native hover menu, and contains both the market list and detail view.
_Avoid_: Context menu, dashboard

**Detail view**:
The richer-data state that replaces the list inside the market panel until the user returns. Its historical series loads only after row activation. A China row also becomes the watched instrument; a metric row does not.
_Avoid_: Separate window, quote card

**Active row**:
The highlighted market row whose detail was most recently opened. It is distinct from the watched instrument because a metric can be active without driving the pet.
_Avoid_: Watched instrument, hover state

**Market reaction**:
The pet's `FLAT`, `RISE`, `SURGE`, or `FALL` presentation driven by the watched instrument's validated percentage change.
_Avoid_: Detail state, active row

**High-volatility alert**:
A small persistent badge beside the pet indicating unusually large expected S&P 500 movement from VIX. It remains visible while the market panel is closed, opens VIX detail when clicked, never changes the market reaction or predicts a crash, and for China instruments is global/US context rather than a China-risk measure.
_Avoid_: PANIC state, market direction, crash forecast

**Metric**:
An independent market measurement, such as VIX, that does not currently drive the pet's watched-instrument reaction.
_Avoid_: Watched instrument, index preset

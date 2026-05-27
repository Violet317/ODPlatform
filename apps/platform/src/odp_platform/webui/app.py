from __future__ import annotations

import logging
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[2]))

import gradio as gr

from odp_platform.common.logging_utils import get_logger
from odp_platform.common.paths import LOGGING_DIR
from odp_platform.webui.config_tab import create_config_ui
from odp_platform.webui.dashboard import create_dashboard_ui
from odp_platform.webui.dataset_analysis import create_dataset_analysis_ui
from odp_platform.webui.dataset_browser import create_dataset_browser_ui
from odp_platform.webui.model_demo import create_model_demo_ui
from odp_platform.webui.training_tab import create_training_ui
from odp_platform.webui.user_tabs import (
    create_detection_results_ui,
    create_image_detection_ui,
    create_llm_chat_ui,
    create_model_selection_ui,
    create_user_info_ui,
)
from odp_platform.webui.validation_tab import create_validation_ui

logger = logging.getLogger(__name__)

ADMIN_PASSWORD = "0000"
BACKEND_URL = "http://127.0.0.1:8000"
BACKEND_DIR = ROOT_DIR / "apps" / "web-backend"

ASSETS_DIR = Path(__file__).resolve().parent / "assets"
WALLPAPER_PATH = ASSETS_DIR / "wallpaper-prism.png"
WALLPAPER_URL = f"/gradio_api/file={WALLPAPER_PATH.as_posix()}"

APP_CSS = """
:root {
  --odp-text: #17182b;
  --odp-muted: #8d93a6;
  --odp-page: #f7f8fc;
  --odp-card: #ffffff;
  --odp-line: #e7eaf2;
  --odp-soft: #f1f3fb;
  --odp-blue: #5368f6;
  --odp-blue-soft: #eef1ff;
  --odp-purple: #8b5cf6;
  --odp-purple-soft: #f1eaff;
  --odp-pink: #db4b8f;
  --odp-pink-soft: #fdebf5;
  --odp-green: #0f766e;
  --odp-green-soft: #e7fbf5;
  --odp-yellow: #d97706;
  --odp-yellow-soft: #fff4d8;
  --odp-sidebar: 246px;
  --odp-sidebar-mini: 88px;
  --odp-topbar: 82px;
  --odp-content-pad-x: 42px;
  --odp-radius: 18px;
}

*,
*::before,
*::after {
  box-sizing: border-box !important;
}

html,
body,
gradio-app,
.gradio-container {
  min-height: 100vh !important;
  overflow-x: hidden !important;
  color: var(--odp-text) !important;
  background: var(--odp-page) !important;
  font-family: Inter, -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "Segoe UI", sans-serif !important;
  text-shadow: none !important;
}

gradio-app,
.gradio-container,
main.app,
main.app > .wrap,
main.app > .wrap > .contain,
main.app > .wrap > .contain > .column {
  width: 100vw !important;
  max-width: none !important;
  margin: 0 !important;
  padding: 0 !important;
  background: transparent !important;
}

.gradio-container::before,
footer {
  display: none !important;
}

.odp-shell {
  position: relative !important;
  z-index: 1 !important;
  width: 100vw !important;
  min-height: 100vh !important;
  margin: 0 !important;
  padding: 0 !important;
  overflow-x: hidden !important;
  background:
    radial-gradient(circle at 78% 12%, rgba(83, 104, 246, 0.08), transparent 24%),
    linear-gradient(180deg, #fbfcff 0%, var(--odp-page) 38%, #f4f6fb 100%) !important;
}

.odp-shell::before {
  content: "";
  position: fixed;
  top: 0;
  right: 0;
  left: var(--odp-sidebar);
  z-index: 16;
  height: var(--odp-topbar);
  border-bottom: 1px solid var(--odp-line);
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 0 10px 28px rgba(23, 24, 43, 0.03);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  transition: left 180ms ease;
}

.tabs,
.tabitem,
.tabitem > .column,
.tabitem > .column > .form,
.form,
.row,
.column,
.gap,
.contain {
  min-width: 0 !important;
  border: 0 !important;
  background: transparent !important;
  box-shadow: none !important;
  overflow: visible !important;
}

.tabs {
  position: relative !important;
  z-index: 2 !important;
  display: block !important;
  width: calc(100vw - var(--odp-sidebar)) !important;
  max-width: calc(100vw - var(--odp-sidebar)) !important;
  min-height: 100vh !important;
  margin-left: var(--odp-sidebar) !important;
  padding: 122px var(--odp-content-pad-x) 56px !important;
  transition: margin-left 180ms ease, width 180ms ease, max-width 180ms ease, padding 180ms ease;
}

.tabitem {
  width: 100% !important;
  max-width: 100% !important;
}

.block,
.panel,
.tabitem > .column > button,
.odp-row > button {
  color: var(--odp-text) !important;
  border: 1px solid var(--odp-line) !important;
  border-radius: var(--odp-radius) !important;
  background: var(--odp-card) !important;
  box-shadow: 0 12px 30px rgba(23, 24, 43, 0.055) !important;
  text-shadow: none !important;
  backdrop-filter: none !important;
  -webkit-backdrop-filter: none !important;
}

.block:hover,
.panel:hover,
.block:focus-within,
.panel:focus-within {
  outline: 0 !important;
  box-shadow: 0 12px 30px rgba(23, 24, 43, 0.055) !important;
}

.block.odp-title {
  position: fixed !important;
  top: 0 !important;
  left: 0 !important;
  z-index: 40 !important;
  width: var(--odp-sidebar) !important;
  height: var(--odp-topbar) !important;
  min-height: var(--odp-topbar) !important;
  padding: 0 22px !important;
  border: 0 !important;
  border-right: 1px solid var(--odp-line) !important;
  border-radius: 0 !important;
  background: rgba(255, 255, 255, 0.94) !important;
  box-shadow: none !important;
}

.odp-title-art {
  display: flex;
  align-items: center;
  gap: 14px;
  width: 100%;
  color: var(--odp-text);
}

.odp-logo-mark {
  position: relative;
  display: inline-block;
  flex: 0 0 36px;
  width: 36px;
  height: 36px;
  border-radius: 12px;
  background: linear-gradient(135deg, #17182b 0%, #17182b 42%, #5368f6 43%, #5368f6 100%);
  box-shadow: 0 10px 24px rgba(83, 104, 246, 0.16);
}

.odp-logo-mark::after {
  content: "";
  position: absolute;
  left: 8px;
  top: 8px;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #ff6ead;
  box-shadow: 10px 8px 0 #54d0ff;
}

.odp-brand-copy {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 2px;
}

.odp-brand-copy strong {
  overflow: hidden;
  color: var(--odp-text);
  font-size: 20px;
  font-weight: 900;
  letter-spacing: 0;
  line-height: 1.1;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.odp-brand-copy small {
  overflow: hidden;
  color: var(--odp-muted);
  font-size: 11px;
  font-weight: 700;
  line-height: 1.1;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.odp-sidebar-toggle {
  position: fixed !important;
  top: 22px !important;
  left: calc(var(--odp-sidebar) - 22px) !important;
  z-index: 60 !important;
  display: grid !important;
  place-items: center !important;
  width: 44px !important;
  min-width: 44px !important;
  max-width: 44px !important;
  height: 44px !important;
  min-height: 44px !important;
  max-height: 44px !important;
  padding: 0 !important;
  border: 1px solid var(--odp-line) !important;
  border-radius: 50% !important;
  background: var(--odp-card) !important;
  color: #7d8496 !important;
  box-shadow: 0 10px 26px rgba(23, 24, 43, 0.08) !important;
  font-size: 18px !important;
  line-height: 1 !important;
  text-shadow: none !important;
  transform: none !important;
  transition: left 180ms ease, background 140ms ease, color 140ms ease, box-shadow 140ms ease !important;
}

.odp-sidebar-toggle:hover,
.odp-sidebar-toggle:focus,
.odp-sidebar-toggle:focus-visible {
  outline: 0 !important;
  background: var(--odp-blue-soft) !important;
  color: var(--odp-blue) !important;
  box-shadow: 0 10px 26px rgba(83, 104, 246, 0.16) !important;
  transform: none !important;
}

.block.odp-sidebar-toggle-wrap,
.odp-sidebar-toggle-wrap,
.odp-sidebar-toggle-wrap > div {
  width: 0 !important;
  height: 0 !important;
  min-height: 0 !important;
  padding: 0 !important;
  margin: 0 !important;
  border: 0 !important;
  background: transparent !important;
  box-shadow: none !important;
  overflow: visible !important;
}

.tab-container.visually-hidden {
  display: none !important;
}

.tab-container:not(.visually-hidden),
.tab-nav,
[role="tablist"] {
  position: fixed !important;
  top: var(--odp-topbar) !important;
  bottom: 76px !important;
  left: 0 !important;
  z-index: 28 !important;
  display: flex !important;
  flex-direction: column !important;
  align-items: stretch !important;
  width: var(--odp-sidebar) !important;
  min-width: var(--odp-sidebar) !important;
  max-width: var(--odp-sidebar) !important;
  height: auto !important;
  min-height: 0 !important;
  gap: 10px !important;
  padding: 24px 14px !important;
  margin: 0 !important;
  border: 0 !important;
  border-right: 1px solid var(--odp-line) !important;
  border-radius: 0 !important;
  background: rgba(255, 255, 255, 0.94) !important;
  box-shadow: none !important;
  overflow-y: auto !important;
  overflow-x: hidden !important;
  backdrop-filter: blur(14px) !important;
  -webkit-backdrop-filter: blur(14px) !important;
  transition: width 180ms ease, min-width 180ms ease, max-width 180ms ease, padding 180ms ease !important;
}

.tab-container button,
.tab-nav button,
[role="tablist"] button[role="tab"] {
  position: relative !important;
  display: flex !important;
  align-items: center !important;
  justify-content: flex-start !important;
  gap: 14px !important;
  width: 100% !important;
  height: 58px !important;
  min-height: 58px !important;
  max-height: 58px !important;
  padding: 0 16px !important;
  border: 0 !important;
  border-radius: 14px !important;
  background: transparent !important;
  color: #767b8d !important;
  box-shadow: none !important;
  font-size: 16px !important;
  font-weight: 800 !important;
  text-shadow: none !important;
  transform: none !important;
}

.tab-container button::after,
.tab-nav button::after,
[role="tablist"] button[role="tab"]::after {
  display: none !important;
  content: none !important;
}

.tab-container button::before,
.tab-nav button::before,
[role="tablist"] button[role="tab"]::before {
  display: grid;
  place-items: center;
  flex: 0 0 34px;
  width: 34px;
  height: 34px;
  border-radius: 10px;
  background: var(--odp-blue-soft);
  color: var(--odp-blue);
  font-size: 17px;
  line-height: 1;
}

.tab-container button:nth-child(1)::before,
.tab-nav button:nth-child(1)::before,
[role="tablist"] button[role="tab"]:nth-child(1)::before {
  content: "⌂";
}

.tab-container button:nth-child(2)::before,
.tab-nav button:nth-child(2)::before,
[role="tablist"] button[role="tab"]:nth-child(2)::before {
  content: "◎";
  background: var(--odp-purple-soft);
  color: var(--odp-purple);
}

.tab-container button:nth-child(3)::before,
.tab-nav button:nth-child(3)::before,
[role="tablist"] button[role="tab"]:nth-child(3)::before {
  content: "▣";
}

.tab-container button:nth-child(4)::before,
.tab-nav button:nth-child(4)::before,
[role="tablist"] button[role="tab"]:nth-child(4)::before {
  content: "✦";
  background: var(--odp-pink-soft);
  color: var(--odp-pink);
}

.tab-container button:nth-child(5)::before,
.tab-nav button:nth-child(5)::before,
[role="tablist"] button[role="tab"]:nth-child(5)::before {
  content: "☻";
  background: var(--odp-green-soft);
  color: var(--odp-green);
}

.tab-container button:nth-child(6)::before,
.tab-nav button:nth-child(6)::before,
[role="tablist"] button[role="tab"]:nth-child(6)::before {
  content: "⚙";
  background: var(--odp-yellow-soft);
  color: var(--odp-yellow);
}

.tab-container button:hover,
.tab-nav button:hover,
[role="tablist"] button[role="tab"]:hover,
.tab-container button.selected,
.tab-nav button.selected,
[role="tablist"] button[role="tab"].selected,
.tab-container button[aria-selected="true"],
.tab-nav button[aria-selected="true"],
[role="tablist"] button[role="tab"][aria-selected="true"] {
  background: var(--odp-blue-soft) !important;
  color: var(--odp-blue) !important;
  box-shadow: none !important;
  transform: none !important;
}

.odp-mode-bar {
  position: fixed !important;
  left: 0 !important;
  bottom: 0 !important;
  z-index: 30 !important;
  display: flex !important;
  align-items: center !important;
  justify-content: flex-end !important;
  width: var(--odp-sidebar) !important;
  height: 76px !important;
  padding: 12px 14px !important;
  margin: 0 !important;
  border: 0 !important;
  border-top: 1px solid var(--odp-line) !important;
  border-right: 1px solid var(--odp-line) !important;
  border-radius: 0 !important;
  background: rgba(255, 255, 255, 0.94) !important;
  box-shadow: none !important;
  backdrop-filter: blur(14px) !important;
  -webkit-backdrop-filter: blur(14px) !important;
  transition: width 180ms ease, padding 180ms ease !important;
}

.odp-mode-bar > div,
.odp-mode-bar > .form {
  display: flex !important;
  justify-content: flex-end !important;
  width: 100% !important;
  border: 0 !important;
  background: transparent !important;
  box-shadow: none !important;
}

.odp-mode-bar button,
.odp-gear-button,
button.odp-gear-button {
  flex: 0 0 48px !important;
  width: 48px !important;
  min-width: 48px !important;
  max-width: 48px !important;
  height: 48px !important;
  min-height: 48px !important;
  max-height: 48px !important;
  padding: 0 !important;
  margin-left: auto !important;
  border: 0 !important;
  border-radius: 14px !important;
  background: var(--odp-soft) !important;
  color: #70778a !important;
  box-shadow: none !important;
  text-shadow: none !important;
  transform: none !important;
}

.odp-mode-bar button:hover,
.odp-gear-button:hover,
button.odp-gear-button:hover {
  background: var(--odp-blue-soft) !important;
  color: var(--odp-blue) !important;
  transform: none !important;
}

html.odp-sidebar-collapsed .odp-shell::before,
.odp-shell.odp-sidebar-collapsed::before {
  left: var(--odp-sidebar-mini);
}

html.odp-sidebar-collapsed .block.odp-title,
html.odp-sidebar-collapsed .tab-container:not(.visually-hidden),
html.odp-sidebar-collapsed .tab-nav,
html.odp-sidebar-collapsed [role="tablist"],
html.odp-sidebar-collapsed .odp-mode-bar,
.odp-shell.odp-sidebar-collapsed .block.odp-title,
.odp-shell.odp-sidebar-collapsed .tab-container:not(.visually-hidden),
.odp-shell.odp-sidebar-collapsed .tab-nav,
.odp-shell.odp-sidebar-collapsed [role="tablist"],
.odp-shell.odp-sidebar-collapsed .odp-mode-bar {
  width: var(--odp-sidebar-mini) !important;
  min-width: var(--odp-sidebar-mini) !important;
  max-width: var(--odp-sidebar-mini) !important;
}

html.odp-sidebar-collapsed .block.odp-title,
.odp-shell.odp-sidebar-collapsed .block.odp-title {
  padding: 0 18px !important;
}

html.odp-sidebar-collapsed .odp-brand-copy,
.odp-shell.odp-sidebar-collapsed .odp-brand-copy {
  display: none !important;
}

html.odp-sidebar-collapsed .odp-title-art,
html.odp-sidebar-collapsed .odp-mode-bar,
.odp-shell.odp-sidebar-collapsed .odp-title-art,
.odp-shell.odp-sidebar-collapsed .odp-mode-bar {
  justify-content: center !important;
}

html.odp-sidebar-collapsed .odp-sidebar-toggle,
.odp-shell.odp-sidebar-collapsed .odp-sidebar-toggle {
  left: calc(var(--odp-sidebar-mini) - 22px) !important;
}

html.odp-sidebar-collapsed .tab-container:not(.visually-hidden),
html.odp-sidebar-collapsed .tab-nav,
html.odp-sidebar-collapsed [role="tablist"],
.odp-shell.odp-sidebar-collapsed .tab-container:not(.visually-hidden),
.odp-shell.odp-sidebar-collapsed .tab-nav,
.odp-shell.odp-sidebar-collapsed [role="tablist"] {
  padding: 24px 14px !important;
}

html.odp-sidebar-collapsed .tab-container button,
html.odp-sidebar-collapsed .tab-nav button,
html.odp-sidebar-collapsed [role="tablist"] button[role="tab"],
.odp-shell.odp-sidebar-collapsed .tab-container button,
.odp-shell.odp-sidebar-collapsed .tab-nav button,
.odp-shell.odp-sidebar-collapsed [role="tablist"] button[role="tab"] {
  justify-content: center !important;
  padding: 0 !important;
  font-size: 0 !important;
}

html.odp-sidebar-collapsed .tab-container button::before,
html.odp-sidebar-collapsed .tab-nav button::before,
html.odp-sidebar-collapsed [role="tablist"] button[role="tab"]::before,
.odp-shell.odp-sidebar-collapsed .tab-container button::before,
.odp-shell.odp-sidebar-collapsed .tab-nav button::before,
.odp-shell.odp-sidebar-collapsed [role="tablist"] button[role="tab"]::before {
  margin: 0 !important;
  font-size: 17px !important;
}

html.odp-sidebar-collapsed .odp-mode-bar button,
html.odp-sidebar-collapsed .odp-gear-button,
.odp-shell.odp-sidebar-collapsed .odp-mode-bar button,
.odp-shell.odp-sidebar-collapsed .odp-gear-button {
  margin: 0 auto !important;
}

html.odp-sidebar-collapsed .tabs,
html.odp-sidebar-collapsed .odp-admin-head,
.odp-shell.odp-sidebar-collapsed .tabs,
.odp-shell.odp-sidebar-collapsed .odp-admin-head {
  width: calc(100vw - var(--odp-sidebar-mini)) !important;
  max-width: calc(100vw - var(--odp-sidebar-mini)) !important;
  margin-left: var(--odp-sidebar-mini) !important;
}

.odp-row {
  display: grid !important;
  width: 100% !important;
  gap: 20px !important;
  align-items: stretch !important;
  margin: 0 0 20px !important;
}

.odp-row > * {
  min-width: 0 !important;
  width: 100% !important;
}

.odp-row > .form {
  display: contents !important;
}

.odp-row > .form > * {
  min-width: 0 !important;
  width: 100% !important;
}

.odp-row > .block,
.odp-row > .form > .block,
.odp-row > button,
.odp-row > .form > button {
  min-height: 98px !important;
}

.odp-row-action {
  grid-template-columns: minmax(220px, 0.65fr) minmax(360px, 2fr) !important;
}

.odp-row-two {
  grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
}

.odp-row-three {
  grid-template-columns: repeat(3, minmax(0, 1fr)) !important;
}

.odp-row-four {
  grid-template-columns: repeat(4, minmax(0, 1fr)) !important;
}

.odp-row-five {
  grid-template-columns: repeat(5, minmax(0, 1fr)) !important;
}

button {
  color: var(--odp-text) !important;
  border: 1px solid var(--odp-line) !important;
  border-radius: 14px !important;
  background: var(--odp-card) !important;
  box-shadow: 0 8px 20px rgba(23, 24, 43, 0.04) !important;
  font-weight: 800 !important;
  text-shadow: none !important;
  transform: none !important;
}

button:hover,
button:focus,
button:focus-visible,
button:not(.odp-sidebar-toggle):hover,
button:not(.odp-sidebar-toggle):active {
  outline: 0 !important;
  background: var(--odp-blue-soft) !important;
  color: var(--odp-blue) !important;
  box-shadow: 0 8px 20px rgba(83, 104, 246, 0.08) !important;
  transform: none !important;
}

button.primary,
button.primary:hover,
.primary button,
.primary button:hover {
  border-color: var(--odp-blue) !important;
  background: var(--odp-blue) !important;
  color: #ffffff !important;
}

.label-wrap,
.label-wrap *,
.block label,
.block span,
.panel label,
.panel span,
.prose,
.markdown,
.markdown p {
  color: var(--odp-text) !important;
  border: 0 !important;
  background: transparent !important;
  box-shadow: none !important;
  text-shadow: none !important;
}

.label-wrap {
  padding: 14px 18px 4px !important;
}

input,
textarea,
select,
.input-container,
.container.show_textbox_border {
  color: var(--odp-text) !important;
  border: 1px solid transparent !important;
  border-radius: 14px !important;
  background: var(--odp-soft) !important;
  box-shadow: none !important;
  text-shadow: none !important;
}

.wrap,
.wrap-inner,
.secondary-wrap {
  border-color: transparent !important;
  background: transparent !important;
  box-shadow: none !important;
}

input:focus,
textarea:focus,
select:focus,
button:focus,
button:focus-visible {
  outline: 0 !important;
}

textarea {
  resize: none !important;
}

ul.options,
ul.options[role="listbox"] {
  z-index: 10000 !important;
  max-height: min(280px, 42vh) !important;
  margin-top: 8px !important;
  padding: 8px !important;
  transform: none !important;
  border: 1px solid var(--odp-line) !important;
  border-radius: 14px !important;
  background: #ffffff !important;
  box-shadow: 0 18px 44px rgba(23, 24, 43, 0.14) !important;
  color: var(--odp-text) !important;
  backdrop-filter: none !important;
  -webkit-backdrop-filter: none !important;
}

ul.options li,
ul.options [role="option"] {
  min-height: 36px !important;
  padding: 8px 10px !important;
  border-radius: 10px !important;
  color: var(--odp-text) !important;
  white-space: nowrap !important;
  word-break: keep-all !important;
  writing-mode: horizontal-tb !important;
  text-shadow: none !important;
}

ul.options li:hover,
ul.options [role="option"]:hover,
ul.options li[aria-selected="true"],
ul.options [role="option"][aria-selected="true"] {
  background: var(--odp-blue-soft) !important;
  color: var(--odp-blue) !important;
}

.image-container,
.upload-container,
.image-container *,
.upload-container * {
  outline: 0 !important;
  box-shadow: none !important;
}

.image-container,
.upload-container {
  background: transparent !important;
}

.dataframe,
.table-wrap,
table,
thead,
tbody,
tr,
td,
th {
  color: var(--odp-text) !important;
  background: transparent !important;
  box-shadow: none !important;
  text-shadow: none !important;
}

th,
td {
  border-color: var(--odp-line) !important;
}

.table-wrap th button,
.table-container button,
.dataframe button {
  border: 0 !important;
  background: transparent !important;
  color: var(--odp-text) !important;
  box-shadow: none !important;
  transform: none !important;
}

.odp-admin-head {
  position: relative !important;
  z-index: 2 !important;
  display: grid !important;
  grid-template-columns: 1fr minmax(180px, 260px) !important;
  gap: 18px !important;
  align-items: end !important;
  width: calc(100vw - var(--odp-sidebar)) !important;
  max-width: calc(100vw - var(--odp-sidebar)) !important;
  margin-left: var(--odp-sidebar) !important;
  padding: 98px var(--odp-content-pad-x) 12px !important;
  transition: margin-left 180ms ease, width 180ms ease, max-width 180ms ease !important;
}

.odp-admin-title {
  min-height: 54px !important;
  display: flex !important;
  align-items: center !important;
  padding: 0 !important;
  border: 0 !important;
  background: transparent !important;
  box-shadow: none !important;
  color: var(--odp-text) !important;
  font-size: 21px !important;
  font-weight: 900 !important;
}

.odp-admin-title-card {
  display: inline-flex !important;
  align-items: center !important;
  gap: 14px !important;
  min-height: 54px !important;
  padding: 0 !important;
  color: var(--odp-text) !important;
}

.odp-admin-title-card::before {
  content: "";
  width: 10px !important;
  height: 34px !important;
  border-radius: 999px !important;
  background: linear-gradient(180deg, var(--odp-blue), #7c5cff) !important;
  box-shadow: 0 10px 24px rgba(83, 104, 246, 0.22) !important;
}

.odp-admin-title-card span {
  display: block !important;
  font-size: 26px !important;
  line-height: 1 !important;
  font-weight: 950 !important;
  letter-spacing: 0 !important;
}

.odp-admin-title-card small {
  display: block !important;
  margin-top: 6px !important;
  color: var(--odp-muted) !important;
  font-size: 12px !important;
  line-height: 1.1 !important;
  font-weight: 800 !important;
}

.odp-admin-layer .tabs {
  min-height: calc(100vh - 154px) !important;
  padding-top: 12px !important;
  padding-bottom: 36px !important;
}

.odp-admin-layer .tabitem {
  padding-top: 0 !important;
}

.odp-admin-layer .odp-row {
  gap: 14px !important;
  margin-bottom: 14px !important;
}

.odp-admin-layer .odp-row > .block,
.odp-admin-layer .odp-row > .form > .block,
.odp-admin-layer .odp-row > button,
.odp-admin-layer .odp-row > .form > button {
  min-height: 92px !important;
}

.odp-admin-layer .odp-row > .block:has(.input-container),
.odp-admin-layer .odp-row > .form > .block:has(.input-container),
.odp-admin-layer .odp-row > .block:has(input),
.odp-admin-layer .odp-row > .form > .block:has(input),
.odp-admin-layer .odp-row > .block:has(select),
.odp-admin-layer .odp-row > .form > .block:has(select),
.odp-admin-layer .odp-row > .block:has([role="radiogroup"]),
.odp-admin-layer .odp-row > .form > .block:has([role="radiogroup"]) {
  min-height: 112px !important;
}

.odp-admin-layer .block,
.odp-admin-layer .panel {
  border-radius: 16px !important;
}

.odp-admin-layer .label-wrap {
  padding: 10px 14px 2px !important;
}

.odp-admin-layer input,
.odp-admin-layer textarea,
.odp-admin-layer select,
.odp-admin-layer .input-container,
.odp-admin-layer .container.show_textbox_border {
  min-height: 48px !important;
  border-radius: 12px !important;
}

.odp-admin-layer button {
  min-height: 52px !important;
  border-radius: 14px !important;
}

.odp-admin-modal {
  position: fixed !important;
  inset: 0 !important;
  z-index: 20000 !important;
  display: grid !important;
  place-items: center !important;
  padding: 24px !important;
  border: 0 !important;
  border-radius: 0 !important;
  background: rgba(248, 250, 255, 0.92) !important;
  box-shadow: none !important;
  backdrop-filter: blur(8px) !important;
  -webkit-backdrop-filter: blur(8px) !important;
}

.odp-admin-modal .odp-modal-card {
  width: min(390px, calc(100vw - 48px)) !important;
  max-width: min(390px, calc(100vw - 48px)) !important;
  padding: 20px !important;
  gap: 12px !important;
  border: 1px solid var(--odp-line) !important;
  border-radius: 22px !important;
  background: #ffffff !important;
  box-shadow: 0 28px 80px rgba(23, 24, 43, 0.13) !important;
  backdrop-filter: none !important;
  -webkit-backdrop-filter: none !important;
}

.odp-admin-modal .odp-modal-card,
.odp-admin-modal .odp-modal-card > *,
.odp-admin-modal .odp-modal-card > * > *,
.odp-admin-modal .odp-modal-card > * > * > * {
  background-color: transparent !important;
}

.odp-admin-modal .odp-modal-card {
  background: #ffffff !important;
}

.odp-admin-modal .odp-modal-card .block,
.odp-admin-modal .odp-modal-card .form,
.odp-admin-modal .odp-modal-card .panel,
.odp-admin-modal .odp-modal-card .wrap,
.odp-admin-modal .odp-modal-card .wrap-inner,
.odp-admin-modal .odp-modal-card .input-container,
.odp-admin-modal .odp-modal-card .container.show_textbox_border {
  min-height: 0 !important;
  padding: 0 !important;
  border: 0 !important;
  background: transparent !important;
  box-shadow: none !important;
}

.odp-admin-modal .odp-modal-card .label-wrap {
  padding: 0 0 8px !important;
}

.odp-admin-modal input,
.odp-admin-modal textarea,
.odp-admin-modal .container.show_textbox_border {
  min-height: 44px !important;
  border: 1px solid var(--odp-line) !important;
  border-radius: 13px !important;
  background: #ffffff !important;
}

.odp-admin-modal input,
.odp-admin-modal textarea {
  padding: 0 14px !important;
}

.odp-admin-modal button {
  min-height: 48px !important;
  border-radius: 15px !important;
}

.odp-admin-modal button:not(.primary) {
  background: #ffffff !important;
}

.odp-admin-modal button.primary,
.odp-admin-modal .primary button {
  background: var(--odp-blue) !important;
  color: #ffffff !important;
}

.odp-modal-actions {
  grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
}

@media (max-width: 1180px) {
  .odp-row-action,
  .odp-row-three,
  .odp-row-four,
  .odp-row-five {
    grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
  }
}

@media (max-width: 820px) {
  .tabs,
  html.odp-sidebar-collapsed .tabs,
  .odp-admin-head,
  html.odp-sidebar-collapsed .odp-admin-head {
    width: calc(100vw - var(--odp-sidebar-mini)) !important;
    max-width: calc(100vw - var(--odp-sidebar-mini)) !important;
    margin-left: var(--odp-sidebar-mini) !important;
    padding-left: 22px !important;
    padding-right: 22px !important;
  }

  .block.odp-title,
  .tab-container:not(.visually-hidden),
  .tab-nav,
  [role="tablist"],
  .odp-mode-bar {
    width: var(--odp-sidebar-mini) !important;
    min-width: var(--odp-sidebar-mini) !important;
    max-width: var(--odp-sidebar-mini) !important;
  }

  .odp-brand-copy {
    display: none !important;
  }

  .odp-sidebar-toggle {
    left: calc(var(--odp-sidebar-mini) - 22px) !important;
  }

  .odp-row,
  .odp-row-action,
  .odp-row-two,
  .odp-row-three,
  .odp-row-four,
  .odp-row-five,
  .odp-admin-head {
    grid-template-columns: 1fr !important;
  }
}
"""


def _show_admin_dialog() -> tuple[gr.update, gr.update, gr.update]:
    return gr.update(visible=True), gr.update(value=""), gr.update(value="")


def _hide_admin_dialog() -> tuple[gr.update, gr.update, gr.update]:
    return gr.update(visible=False), gr.update(value=""), gr.update(value="")


def _try_enter_admin(password: str) -> tuple[gr.update, gr.update, gr.update, gr.update, gr.update]:
    if (password or "").strip() == ADMIN_PASSWORD:
        return (
            gr.update(visible=False),
            gr.update(visible=True),
            gr.update(visible=False),
            gr.update(value=""),
            gr.update(value=""),
        )
    return (
        gr.update(),
        gr.update(),
        gr.update(visible=True),
        gr.update(value=""),
        gr.update(value="密码错误"),
    )


def _return_user_mode() -> tuple[gr.update, gr.update, gr.update, gr.update, gr.update]:
    return (
        gr.update(visible=True),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(value=""),
        gr.update(value=""),
    )


def _create_user_tabs() -> None:
    with gr.Tabs():
        with gr.TabItem("图像检测"):
            create_image_detection_ui()
        with gr.TabItem("检测结果"):
            create_detection_results_ui()
        with gr.TabItem("模型选择"):
            create_model_selection_ui()
        with gr.TabItem("LLM对话"):
            create_llm_chat_ui()
        with gr.TabItem("用户信息"):
            create_user_info_ui()


def _create_admin_tabs() -> None:
    with gr.Tabs():
        with gr.TabItem("Dashboard"):
            create_dashboard_ui()
        with gr.TabItem("数据集浏览"):
            create_dataset_browser_ui()
        with gr.TabItem("训练"):
            create_training_ui()
        with gr.TabItem("模型演示"):
            create_model_demo_ui()
        with gr.TabItem("数据校验"):
            create_validation_ui()
        with gr.TabItem("配置管理"):
            create_config_ui()


def create_app() -> gr.Blocks:
    get_logger(
        base_path=LOGGING_DIR,
        log_type="webui",
        log_level=logging.INFO,
        logger_name="odp-webui",
    )
    logger.info("创建低空智瞰 Gradio UI")

    with gr.Blocks(
        title="低空智瞰",
        theme=gr.themes.Soft(primary_hue="blue", neutral_hue="slate"),
        css=APP_CSS,
    ) as app:
        with gr.Column(elem_classes=["odp-shell"]):
            gr.HTML(
                """
                <button
                    type="button"
                    class="odp-sidebar-toggle"
                    aria-label="切换边栏"
                    aria-expanded="true"
                    onclick="
                        const root = document.documentElement;
                        const shell = document.querySelector('.odp-shell');
                        const collapsed = shell
                            ? shell.classList.toggle('odp-sidebar-collapsed')
                            : root.classList.toggle('odp-sidebar-collapsed');
                        root.classList.toggle('odp-sidebar-collapsed', collapsed);
                        this.setAttribute('aria-expanded', String(!collapsed));
                    "
                >☰</button>
                """,
                elem_classes=["odp-sidebar-toggle-wrap"],
            )
            gr.HTML(
                """
                <section class="odp-title-art" aria-label="低空智瞰 航拍智能目标识别与检测系统">
                    <span class="odp-logo-mark" aria-hidden="true"></span>
                    <span class="odp-brand-copy">
                        <strong>低空智瞰</strong>
                        <small>航拍智能目标识别与检测系统</small>
                    </span>
                </section>
                """,
                elem_classes=["odp-title"],
            )
            with gr.Column(visible=True) as user_layer:
                with gr.Row(elem_classes=["odp-mode-bar"]):
                    admin_entry_btn = gr.Button("⚙️", elem_classes=["odp-gear-button"])
                _create_user_tabs()

            with gr.Column(visible=False, elem_classes=["odp-admin-layer"]) as admin_layer:
                with gr.Row(elem_classes=["odp-admin-head"]):
                    gr.HTML(
                        """
                        <div class="odp-admin-title-card">
                            <div>
                                <span>管理员工作台</span>
                                <small>低空智瞰 · 系统配置与模型运维</small>
                            </div>
                        </div>
                        """,
                        elem_classes=["odp-admin-title"],
                    )
                    return_user_btn = gr.Button("返回用户模式")
                _create_admin_tabs()

            with gr.Column(visible=False, elem_classes=["odp-admin-modal"]) as admin_dialog:
                with gr.Group(elem_classes=["odp-modal-card"]):
                    admin_password = gr.Textbox(
                        label="管理员密码",
                        type="password",
                        placeholder="请输入密码",
                        max_lines=1,
                    )
                    admin_error = gr.Textbox(
                        label="状态",
                        value="",
                        interactive=False,
                        max_lines=1,
                    )
                    with gr.Row(elem_classes=["odp-row", "odp-modal-actions"]):
                        admin_cancel_btn = gr.Button("取消")
                        admin_confirm_btn = gr.Button("进入", variant="primary")

            admin_entry_btn.click(
                fn=_show_admin_dialog,
                outputs=[admin_dialog, admin_password, admin_error],
            )
            admin_cancel_btn.click(
                fn=_hide_admin_dialog,
                outputs=[admin_dialog, admin_password, admin_error],
            )
            admin_confirm_btn.click(
                fn=_try_enter_admin,
                inputs=[admin_password],
                outputs=[user_layer, admin_layer, admin_dialog, admin_password, admin_error],
            )
            admin_password.submit(
                fn=_try_enter_admin,
                inputs=[admin_password],
                outputs=[user_layer, admin_layer, admin_dialog, admin_password, admin_error],
            )
            return_user_btn.click(
                fn=_return_user_mode,
                outputs=[user_layer, admin_layer, admin_dialog, admin_password, admin_error],
            )
    return app


def _ensure_backend_running(timeout: float = 10.0) -> bool:
    """检测后端是否运行，未运行则自动启动。"""
    try:
        urllib.request.urlopen(f"{BACKEND_URL}/health", timeout=1)
        logger.info("后端服务已在运行")
        return True
    except Exception:
        pass

    logger.info("后端未运行，正在自动启动...")
    backend_main = BACKEND_DIR / "main.py"
    if not backend_main.exists():
        logger.warning("找不到后端入口: %s", backend_main)
        return False

    subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"],
        cwd=str(BACKEND_DIR),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
    )

    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen(f"{BACKEND_URL}/health", timeout=1)
            logger.info("后端服务启动成功")
            return True
        except Exception:
            time.sleep(0.5)

    logger.warning("后端服务启动超时（%.0fs），Dashboard 功能暂不可用", timeout)
    return False


def main() -> None:
    create_app().launch(
        server_name="0.0.0.0",
        server_port=7860,
        allowed_paths=[str(ASSETS_DIR)],
    )


if __name__ == "__main__":
    main()

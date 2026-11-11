# MIUI 系统界面（SystemUI）17.03.260226.r · 改包审计

> 对象：`com.android.systemui` 版本 `17.03.260226.r`（Android 17）原版 vs 改版 `MiuiSystemUI.apk`。
> 全部结论来自 apktool 3.0.3 解码态 + 方法级归一化 diff + 资源集合对比，`scripts/` 可一键复现。

## 0. 对象与指纹

| 项 | 原版 | 改版 |
|---|---|---|
| 文件 | `系统界面_17.03.260226.r.apk` | `MiuiSystemUI.apk` |
| 大小 | 52,333,704 B | 52,775,230 B（+441,526 B，+0.84%） |
| MD5 | `7fa0c7b6c0b3b6bcf7b3861d2fbb1dbd` | `f94a649f5b14adaab605b0ddce7c1b09` |
| SHA-256 | `551aa3584bdcffdb5747e10bf6b1c344f0d4b776b617ad3b085e66890e30d5c9` | `4b933b3000049fc4c1f17fad4d11fa40fd749881ba189379e12a9331d3920e9a` |
| 版本 | versionCode `202602260` / versionName `17.03.260226.r` | 未改（`AndroidManifest.xml` 字节级一致） |
| dex | `classes.dex` 11,489,692 / `classes2.dex` 11,554,664 / `classes3.dex` 10,192,156 | 11,642,792 / 11,625,444 / 10,309,844（各 +1.2%） |
| `resources.arsc` | 4,606,804 B | 4,792,648 B（+185,844 B） |
| ZIP 条目 | 9,044 | 9,082（+38，无删除） |
| 签名 | v3 签名，证书 `CN=MIUI, O=Xiaomi`，SHA-256 `c9009d01ebf9f5d0302bc71b2fe9aa9a47a432bba17308a3111b75d7b2149025` | `META-INF/CERT.RSA`、`CERT.SF`、`MANIFEST.MF` 三件套 **CRC 与 MD5 完全一致 → 未重签** |

> `apksigner verify` 对改版报 `v3 CHUNKED_SHA256 digest mismatch`。这是**改包未重签的必然结果**：v3 签名块原样保留，但包内容变了，摘要自然对不上。系统分区的系统界面由平台证书信任，装机时不走这条校验；这也是 `com.android.systemui` 改包的硬约束（重签即无法开机）。

> 附带问题：改版 `resources.arsc` 被 MT 重编后，`aapt dump badging` 报 `ResTable_type entry index to 0x22dd8 extends beyond chunk end`，资源表结构有越界条目。apktool 解码正常，但**任何依赖 aapt/aapt2 的处理链（含 `zipalign` 后的 `aapt` 校验、部分 ROM 工具链）会失败**。

> 原件下载（GitHub Release v1.0.0，仓库本体不放 52MB 二进制）：
> [原版 `系统界面_17.03.260226.r.apk`](https://github.com/mariusarva/miui-systemui-17.03.260226-diff/releases/download/v1.0.0/SystemUI-original-17.03.260226.r.apk) ·
> [改版 `MiuiSystemUI.apk`](https://github.com/mariusarva/miui-systemui-17.03.260226-diff/releases/download/v1.0.0/MiuiSystemUI.apk)
>
> GitHub 会剥离 release 附件名里的非 ASCII 字符，原版附件实际名为 `SystemUI-original-17.03.260226.r.apk`，内容即原文件（SHA-256 见上表）。

## 1. 结论速览

改版在原版基础上做了 **12 组改动**，全部是「既有视图里注入 + 资源换皮」，没有新增 dex、没有改 Manifest、没有重签：

1. **iOS 风左置状态栏图标**（`IosLeftIcons` 6 类 + `MiuiRotateIconInjector` 1 类）
2. **双排运营商 / 信号组件**（`com.carrier.datasim` 46 类，状态栏与锁屏两处）
3. **通知中心头部重构**（标题「通知中心」+ 天气 + 铃铛，日期时间改居中）
4. **天气组件**（`WeatherView` 2 类 + 27 张天气矢量图）
5. **锁屏 PIN 玻璃拟态**（`LockscreenPinGlass` 2 类 + `NumPadKey` / `KeyguardPINView` 注入）
6. **通知毛玻璃与圆角**（5 个 `*GlassEffect` 改写 + 圆角按实际高度取）
7. **状态栏时钟增强**（秒显示开关 + 时钟区手势）
8. **网速显示改造**（`NetworkSpeedView` / `NetworkSpeedController`）
9. **电量百分比 + 电池图标**（`MiuiBatteryMeterView` + 4 个新 drawable）
10. **媒体通知与进度条着色器重构**（布局重排 + 粉紫 AGSL 光晕）
11. **隐私容器改版**（480dp 托底 + 跳转箭头 + 新圆形图标）
12. **控制中心整体尺寸放大 9%**（`-xxhdpi` 83 个 `qs_control_*` dimens 统一 ×1.0909，并补 `-xxxhdpi` 变体）

## 2. 规模数据

| 层 | 指标 | 数值 |
|---|---|---|
| ZIP | 新增 / 删除 / 内容变化 | 38 / 0 / 37 |
| 代码 | 类总数 | 44,183 → 44,240（新增 **57**，删除 0） |
| 代码 | 内容不同类文件 | 244 |
| 代码 | 归一化后**真实改动类** | **53**（191 个是 dex 重编译噪声） |
| 代码 | 新增方法 / 删除方法 / 改动方法 | 21 / 0 / 67 |
| 代码 | 新增类的方法总数 | 455 |
| 资源 | res 文件资源 新增 / 删除 / 变化 | 34 / 0 / 33 |
| 资源 | values 键 新增 / 删除 / 值变化 | 124 / 20 / 146 |
| 资源 | 新增 public 资源 id | 41（含 3 个新 id、30 个天气/图标 drawable、8 个 dimens） |

> 噪声比例 191/244 = **78.3%**。不做归一化的话，改动类会虚报近 4 倍。

## 3. 新增 57 类的分布

| 包 | 类数 | 用途 |
|---|---|---|
| `com.carrier.datasim` | 46 | 双排运营商 / 信号 / 网络类型 / WiFi / VPN / 旋转锁 / 动画补丁 |
| `com.android.systemui.statusbar.phone.ui` | 6 | `IosLeftIcons` 与 5 个内部类（`Kid/Rkid/Fkid/Pre/Poll`） |
| `com.android.keyguard` | 2 | `LockscreenPinGlass` + `FadeAfterPressListener` |
| `com.android.systemui.statusbar` | 2 | `WeatherView` + `WeatherContentObserver` |
| `com.android.systemui.statusbar.phone` | 1 | `MiuiRotateIconInjector` |

## 4. 逐组改动明细

### 4.1 iOS 风左置状态栏图标

新增类：`com.android.systemui.statusbar.phone.ui.IosLeftIcons`（主控）、`$Kid` / `$Rkid` / `$Fkid`（`ViewGroup.OnHierarchyChangeListener`）、`$Pre`（`OnPreDrawListener`）、`$Poll`（`Runnable`）、`MiuiRotateIconInjector`。

| 注入点（既有方法内插 `invoke-static`） | 注入内容 |
|---|---|
| `StatusBarIconControllerImpl.<init>` | `MiuiRotateIconInjector.install` |
| `KeyguardStatusBarViewController.onViewAttached` (+2/-1) | `IosLeftIcons.installKeyguard` |
| `HomeStatusBarViewBinderInjector.showClock / hideClock` (+2/+1) | `IosLeftIcons.installHome / holdHost / setHomeLeftVisible` |
| `HomeStatusBarViewBinderInjector$statusBarStateCallback$1.onStateChanged / onStatePreChange` | 同上，状态切换时重建左组 |
| `StatusBarRootKt$$ExternalSyntheticLambda3.invoke` (+2) | `holdHost` + `installHome`（Compose 入口） |
| `HomeStatusBarIconBlockListInteractor.<init>` (+1/-1) | `IosLeftIcons.rightBlockList()` 替换原生黑名单 |
| `MiuiIconManagerUtils.<clinit>` | 静态 `RIGHT_BLOCK_LIST` 去掉 2 项、加入 `"rotate"` |
| `DarkIconDispatcherExt.getTint / getDarkIntensity` (+5/-2, +2) | 先 `tick()`，左组 `inGroup(view)` 时直接返回原色（避免深浅色切换跳色） |
| `StatusBarIconView.updateIconColor` (+9/-1) | `opPkg=="android"` 或 `AppOpsUtils.isExceptionByTestPolicy(pkg)` 时跳过重着色 |
| `PhoneStatusBarView`、`MiuiKeyguardStatusBarView`、`MiuiPhoneStatusBarPolicy$$ExternalSyntheticLambda1` | 容器挂载与刷新 |

资源：新增 id `system_icons_containerA=0x7f0b0df2`、`system_icons_containerB=0x7f0b0df3`（`values/ids.xml` + `public.xml` 均已登记）；`keyguard_status_bar.xml` 左栏容器 `FrameLayout` → `LinearLayout`。

### 4.2 双排运营商 / 信号组件（`com.carrier.datasim`）

| 组 | 类 |
|---|---|
| 状态源 | `SimStateRepo`（4 个内部回调 + `Listener`）、`SlotMethodCache` |
| 文案 | `CustomCarrierNames`、`SimCarrierView`、`DataSimCarrierView`、`NonDataSimCarrierView`、`AirplaneModeCustomTextView`、`AirplaneModeCustomTextView2`、`SimAirplaneTextView` |
| 信号 | `SimSignalView`、`DataSimSignalView`、`NonDataSimSignalView`（均带 API31 `SignalCallback` 与非 API31 回退） |
| 网络类型 | `DataSimNetworkTypeView`、`NonDataSimNetworkTypeView`、`DataSimTypeRegistry` |
| 其它图标 | `WifiSignalView`（`WifiRefreshRunnable`）、`VpnIconView`、`CustomRotationLockView` |
| 布局协调 | `StatusBarRowsCoordinator`（4 个内部 Runnable） |
| 动画补丁 | `CcAnimFix`、`CcAnimEnd` |

注入点与布局：

- `control_center_status_bar.xml` 整文件重写：外层 `ControlCenterStatusBarIcon` 由 `horizontal` 改 `vertical`，内部改为 `datasim_row1`（24dp）+ `datasim_row2`（25dp）双 `FrameLayout`，行1 放数据卡信号/运营商/网络类型/WiFi/VPN，行2 放非数据卡三件套 + `datasim_icons_dual` 图标组，尾部 `StatusBarRowsCoordinator`（0dp×5dp）。
- `keyguard_status_bar.xml` 新增 `keyguard_datasim_carrier`（`0x7f0b0df4`，`DataSimCarrierView`，14sp/白）。
- `status_bar_mobile_signal_group_inner.xml`：`mobile_type_single` 移到容器末尾并固定 13.5sp 粗体 + 3dp/1dp 边距；`mobile_signal` 由固定 `status_bar_icon_height` 改 `wrap_content/match_parent` 并 `constraintStart_toStartOf=parent`；`mobile_left_mobile_inout` 改 `invisible` + 0dp。
- 代码注入：`MiuiMobileIconsInteractorImpl`（`DataSimTypeRegistry.register`）、`ModernStatusBarMobileView.setVisibility`（新增覆写）、`MiuiMobileIconBinder$bind$1$1$15`（+5/-13，新增 `$miuiVM`/`$mobileType` 合成字段）、`MiuiCellularIconVM$mobileTypeSingleVisible$2`（+3/-3）、`ControlCenterStatusBarIcon` 与 `ControlCenterFakeStatusIcons` 各新增 `setAlpha/setTranslationX/setTranslationY/setVisibility` 四个覆写（挂 `CcAnimFix`）。
- 资源：`config_statusBarIcons` 移除 `nfc`、`vpn`；`config_statusBarIconsToExclude` 移除 `rotate`；`data_type_name_default_value` 里 `5GA` 改小体大写 `5Gᴀ`。

### 4.3 通知中心头部重构

`miui_ns_notification_header_view.xml` 整文件重写：

- 根节点加 `layout_marginTop=50dp`。
- `horizontal_time`（`MiuiClockMode=time_date`）改居中（`constraintStart/End=parent`），`marginBottom` 由 dimens 改 `65dp`。
- `date_time` 从底部移到顶部居中，`MiuiClockMode` 由 `date_24` 改 `date_weekday`，`marginTop=10dp`。
- `big_time` 改居中、`layout_height=wrap_content`。
- `carrier_container` 从 `gone / 0dp` 改为可见、`constraintEnd_toStartOf=privacy_container`，内部依次放：`TextView`「通知中心」(24sp bold 白) → 撑开 `View`(weight 1) → 右侧竖排(两个 `WeatherView`：25dp 图标 + 温度) → `ImageView` 24dp `@drawable/bell`(contentDescription「通知图标」) → 原 `MiuiCarrierTextLayout`（改 `gone / start|center`）。

配套代码：

| 类 / 方法 | 改动 |
|---|---|
| `MiuiNotificationHeaderView.updateCarrierText$1` | +5/-38：删掉横竖屏 / pad / tinyScreen 全套 `ConstraintSet.connect` 分支，改固定可见性 + `translationX/Y=0` |
| `NotificationHeaderExpandController.updateTranslationX` | -2 |
| `NotificationHeaderExpandController$notificationCallback$1.onExpansionChanged` | +2/-2 |
| `ControlCenterHeaderExpandController$controlCenterCallback$1.onExpansionChanged` | +4 |
| `ControlCenterHeaderController.updateDimens` / `updateConstraint` | +1/-1、等长替换 |
| `ShadeHeaderClipController.<clinit>` | 裁剪常量 +1/-1 |
| `MiuiKeyguardStatusBarView.updateCarrierVisibility$1` | +7/-14 |
| `notification_dismiss_view_container.xml` | 容器 `alpha=0.001`，「清除全部」按钮 `translationX=158dp`、`translationY=-550dp` 硬叠到铃铛位置 |
| `MiuiMediaViewControllerImpl.onFullAodStateChanged` | +1/-1 |

> 「清除全部」用的是**硬坐标平移**，不是布局绑定。换分辨率 / 换字号会偏位，这是已知失效点。

### 4.4 天气组件 `WeatherView`

- 新类 `com.android.systemui.statusbar.WeatherView` + `$WeatherContentObserver`，ContentObserver 读天气 provider，按天气码取 `weather_icons_*`，点击跳天气 App。
- 新增 30 个 drawable：`weather_icons_0..25`（含 `_0_n`、`_1_n`、`_3_n` 夜间变体）+ `bell`、`leaf`。
- 全部在 `public.xml` 登记（`weather_icons_* = 0x7f08xxxx` 段），否则 `getIdentifier` 拿不到。

### 4.5 锁屏 PIN 玻璃拟态

- 新类 `com.android.keyguard.LockscreenPinGlass` + `$FadeAfterPressListener`。
- `NumPadKey`：新增字段 `mPinGlassOverlay:ImageView`、`mPinGlassHighlightAnimator:Animator`、`mPinGlassBaseRipple:RippleDrawable`；新增 `onWindowFocusChanged(Z)`（清高亮）、`onLayout`；`onTouchEvent` +6（改走 `LockscreenPinGlass.handleTouch`）、`drawableStateChanged` +1/-12（删原 Folme 按压块）、`<init>` +4。
- `KeyguardPINView`：新增 `onLayout(ZIIII)` → `LockscreenPinGlass.applyPasswordRowOffset`；`$appearAnimConfig$1.onUpdate` +3、`onComplete` +1。
- 资源：`finger_circle_image_normal.png` / `_light.webp` / `_aod.webp` 三个变体被替换成 129~132 字节的空壳（等于关闭原指纹圆圈底图）；`num_state_view.xml` 与 `keyguard_pin_view.xml` 调整 `translationY=5dp`、`bouncer_message_area` 上边距改 60dp 等。

### 4.6 通知毛玻璃与圆角

| 类 | 方法 | 改动 |
|---|---|---|
| `HeadsUpNotificationGlassEffect` | `apply` +26/-49，`clear` +1/-47；新增静态 `glassParamsArray:[F` | 改用 `NotificationRowBlurEffect.INSTANCE.apply(...)` + `getResources().getStringArray(...)` → `Float.parseFloat` → `toFloatArray()` |
| `HeadsUpNotificationGlassDarkEffect` | 同上 | 同上 |
| `FocusNotificationGlassEffect` / `FocusNotificationGlassOnKeyguardEffect` / `FocusNotificationGlassOnKeyguardLightWallPaperEffect` | `apply` 各 +3/-3 | 同上接口对齐 |
| `NotificationUtil$1.getOutline` | +5/-2 | 对 `id=0x7f0b0709`（`media_bg`）直接用 `0x7f073000`（`notification_item_bg_radius`）覆盖圆角，其余按 `ExpandableNotificationRow.getActualHeight()` 走 `RoundRectDimensCache` |
| `StackScrollAlgorithm.getScrimTopPaddingOrZero` | 等长替换 | 遮罩顶距 |
| `SharedNotificationContainerInteractor$useExtraShelfSpace$1.invokeSuspend` | -22 | 砍掉额外 shelf 空间分支 |
| `MiuiBaseNotifUtil.shouldSuppressFold` | -1 | 折叠抑制改常量返回 |

颜色（36 个）：文字类统一拉到 `#e6ffffff`（`notification_primary/secondary_text_color_light`、`notification_time_color*`、`action_text`、`optimized_heads_up_*`）；`*_blend_*_color_3` 全部置 `#00000000`（去掉第三层混合）。

尺寸：`notification_item_bg_radius` 新增 26dp、`media_bg_radius` 32dp、`notification_divider_height` 6dp、`notification_panel_margin_top` 0dp、`combined_header_height` 135dp、`combined_blur_max_radius` 30dp、`header_blur_max_radius` 10.909973dp。

### 4.7 状态栏时钟增强

`MiuiClock` 新增 10 个方法 + 4 个字段：

| 新增 | 说明 |
|---|---|
| `isSecondsEnabled()` / `toggleSeconds()` / `applySecondsState(Z)` / `syncSecondsTicker()` / `scheduleTick()` / `run()` / `chain()` / `isInStatusBar()` / `onLongClick(View)` | 秒显示开关，持久化在 `SharedPreferences("clock_seconds")` 的 `enabled` 布尔 |
| 字段 `mSecTickerOn`、`mSwipeDownX/Y`、`mSwipeHandled` | 秒刷新任务与手势状态 |

`updateTime()` +21 行接入秒显示；`updateLightDarkTint$2` +1、`onDetachedFromWindow` +2（注销 ticker）。

`PhoneStatusBarView`：新增 `private handleClockSwipe(MotionEvent)` + 字段 `mClockSwipeX/Y/Handled/OnClock`，在 `dispatchTouchEvent` 首行无条件调用。逻辑：DOWN 时取 `findViewById(0x7f0b027d)`（`@id/clock`）的 `getGlobalVisibleRect` 判断落点是否在时钟上，MOVE 时算 `dx/dy` 与 `16dp × density` 阈值比较，全程 `Log.i("ClockSwipe", ...)`。

`com.miui.clock.classic.ClassicTextAreaView.init` +1/-1、`ClockBean.isColonShow` +1/-1（秒分隔符闪烁跟随秒开关）。

文案：`fmt_time_12hour_minute` `h:mm`→`hh:mm`、`fmt_time_24hour_minute` `H:mm`→`HH:mm`；`status_bar_clock_date_weekday_format*_brief` 改为 `M月d日EEE•YY年N月e`。尺寸：`status_bar_clock_size_new` 13.5dp。

### 4.8 网速显示

- `NetworkSpeedView.updateResources$15` +25/-1、`updateNetworkSpeed$1` +2/-18、`getNetworkSpeedWidth` +3/-3。
- `NetworkSpeedController.<init>` +2/-2、`NetworkSpeedController$5.handleMessage` +2/-5。
- 新增 style `TextAppearance.StatusBar.NetWorkSpeedNumber`、`TextAppearance.StatusBar.NetWorkSpeedUnit`（`public.xml` 未登记，属内部 style）。

### 4.9 电量百分比 + 电池图标

- `MiuiBatteryMeterView`：`updateChargeAndText()`（新增，电量文本拼 `%` + 设置 `contentDescription` + 充电图标 `battery_charging_view` 的 Folme 显隐动画）、`onLayout` +1、`onBatteryStyleChanged` +1。
- 新增 drawable：`ic_battery_charging.xml`、`ic_battery_normal.xml`（34×48dp 矢量）、`battery_progress_drawable.xml`（layer-list）、`ic_battery_*` 全部进 `public.xml`。
- 尺寸：`battery_percent_mark_view_text_size` 13.5dp、`status_bar_battery_percent_size` 13.5dp、`battery_percent_mark_view_padding_top` 0dp；`battery_digital_view.xml` 里 `battery_image` 高度改 `match_parent`、容器 `paddingTop=0dp`。

### 4.10 媒体通知与进度条着色器

- `res/xml/miui_media_session_normal.xml` 重排：`media_seamless` 固定 30×30dp / `top 15dp` / `end 15dp`；`header_title` `marginTop=18dp`；`media_progress_bar` `marginTop=-5dp`、左右各 46dp；时间标签改 8dp；`actions` `marginTop=12dp`，`action0..4` 全部 `layout_width=0dp` 并改成 `end` 链式约束（`action4→action1→action2→action3→action0`）。
- `res/drawable/$ic_media_next__*.xml`、`$ic_media_prev__*.xml` 六个矢量重画。
- `res/raw/music_player_tracker.frag`（AGSL 着色器）：加 `verticalScale=1`、`glowRange=3.0`，进度条填充色改粉紫 `vec3(0.91, 0.71, 0.85)`，`alphaBlend(glow, progressBody)`。
- `MiuiMediaViewControllerImpl.onFullAodStateChanged` +1/-1。

### 4.11 隐私容器改版

`privacy_container.xml`：

- 根容器加 `gravity=center_horizontal / orientation=vertical`，`focusable/clickable` 置 `false`。
- `privacy_chip` 背景去掉 `privacy_container_background`，改固定 `480dp × 0dp`（纯占位）。
- 四个图标 `layout_marginEnd` 改 `layout_marginRight=3dp`。
- `privacy_text` 加 `marginTop=0.5dp`。
- 新增 `ImageView` 16dp `@drawable/privacy_dialog_goto`（跳转箭头）。
- `icon_dot` 加 `alpha=0.0`。

`control_center_header_view.xml`：`normal_privacy_container` 改 `wrap_content` + `marginTop=-10dp` + 四边居中约束；`normal_control_center_carrier_layout` 改 `0dp×0dp` + `ellipsize=marquee` + `style=TextAppearance.QSControl.CarrierText`。

图标：`ic_privacy_icon_camera/location/mic/screen` 四个从 16dp 线性图标改为 58.5dp 圆形彩色底 + 白色图形（mic 为 `#fb9300` 橙底）；`privacy_dialog_goto` 新增；`zen_mode_dark/light` 从 20dp 线性改 24dp / 200 viewport 重画。

### 4.12 控制中心整体放大 9%

- `-xxhdpi` 下 **83 个 `qs_control_*` dimens 统一乘 1.0909（12/11）**，例：`qs_control_big_tile_width` 142.0→154.909dp、`qs_control_big_tile_height` 73.33→80.0dp、`qs_control_detail_width` 297.328→324.359dp、`qs_control_corner_general_radius` 16.0→17.454dp、`qs_control_tiles_indicator_width` 40.0→61.818dp（这一项是 +54%，独立于整体系数）。
- 新增 `-xxxhdpi` 变体 30 个键（原版只有 `-xxhdpi`），即给高分屏补了同值。
- 新增 `-xxhdpi` 键 49 个（原版缺键、只在改版存在），包括 `qs_control_big_tile_corner_radius`、`qs_control_big_tile_status_width`、`qs_control_content_view_margin_right` 等。
- 删除 `-xxhdpi` 键 20 个。
- `values-land/dimen/notification_panel_shade_header_top_padding` 新增 10dp；`-xxhdpi` 同键新增为 100dp。

> 2400×1080 设备走的就是 `-xxhdpi`，所以视觉上控制中心会整体放大 9%。这不是 bug，是刻意做的「大图标」取向；但换机型前必须重新核对。

## 5. 全部 53 个真实改动类

```
com/android/keyguard/KeyguardPINView$appearAnimConfig$1        com/android/keyguard/KeyguardPINView
com/android/keyguard/NumPadKey                                  com/android/keyguard/blur/MiuiKeyguardBlurInteractor$wallpaperBlurRatio$2$1
com/android/keyguard/panel/KeyguardPanelViewController$nsslLockYPosition_delegate$lambda$102$$inlined$combine$1$3
com/android/keyguard/panel/KeyguardPanelViewController          com/android/systemui/controlcenter/phone/widget/ControlCenterFakeStatusIcons
com/android/systemui/controlcenter/phone/widget/ControlCenterStatusBarIcon
com/android/systemui/controlcenter/shade/ControlCenterHeaderController
com/android/systemui/controlcenter/shade/ControlCenterHeaderExpandController$controlCenterCallback$1
com/android/systemui/controlcenter/shade/ControlCenterHeaderExpandController$start$1$1$1
com/android/systemui/controlcenter/shade/NotificationHeaderExpandController$notificationCallback$1
com/android/systemui/controlcenter/shade/NotificationHeaderExpandController
com/android/systemui/qs/MiuiNotificationHeaderView             com/android/systemui/statusbar/DarkIconDispatcherExt
com/android/systemui/statusbar/StatusBarIconView               com/android/systemui/statusbar/StatusBarIslandControllerImpl
com/android/systemui/statusbar/notification/mediacontrol/MiuiMediaViewControllerImpl
com/android/systemui/statusbar/notification/stack/StackScrollAlgorithm
com/android/systemui/statusbar/notification/stack/domain/interactor/SharedNotificationContainerInteractor$useExtraShelfSpace$1
com/android/systemui/statusbar/notification/style/vieweffect/FocusNotificationGlassEffect
com/android/systemui/statusbar/notification/style/vieweffect/FocusNotificationGlassOnKeyguardEffect
com/android/systemui/statusbar/notification/style/vieweffect/FocusNotificationGlassOnKeyguardLightWallPaperEffect
com/android/systemui/statusbar/notification/style/vieweffect/HeadsUpNotificationGlassDarkEffect
com/android/systemui/statusbar/notification/style/vieweffect/HeadsUpNotificationGlassEffect
com/android/systemui/statusbar/notification/utils/NotificationUtil$1
com/android/systemui/statusbar/phone/KeyguardStatusBarViewController
com/android/systemui/statusbar/phone/MiuiIconManagerUtils  com/android/systemui/statusbar/phone/MiuiKeyguardStatusBarView
com/android/systemui/statusbar/phone/MiuiPhoneStatusBarPolicy$$ExternalSyntheticLambda1
com/android/systemui/statusbar/phone/PhoneStatusBarView     com/android/systemui/statusbar/phone/ui/StatusBarIconControllerImpl
com/android/systemui/statusbar/pipeline/mobile/domain/interactor/MiuiMobileIconsInteractorImpl
com/android/systemui/statusbar/pipeline/mobile/ui/binder/MiuiMobileIconBinder$bind$1$1$15
com/android/systemui/statusbar/pipeline/mobile/ui/view/ModernStatusBarMobileView
com/android/systemui/statusbar/pipeline/mobile/ui/viewmodel/MiuiCellularIconVM$mobileTypeSingleVisible$2
com/android/systemui/statusbar/pipeline/shared/domain/interactor/HomeStatusBarIconBlockListInteractor
com/android/systemui/statusbar/pipeline/shared/ui/binder/HomeStatusBarViewBinderInjector$statusBarStateCallback$1
com/android/systemui/statusbar/pipeline/shared/ui/binder/HomeStatusBarViewBinderInjector
com/android/systemui/statusbar/pipeline/shared/ui/composable/StatusBarRootKt$$ExternalSyntheticLambda3
com/android/systemui/statusbar/policy/HDController            com/android/systemui/statusbar/policy/NetworkSpeedController$5
com/android/systemui/statusbar/policy/NetworkSpeedController    com/android/systemui/statusbar/views/MiuiBatteryMeterView
com/android/systemui/statusbar/views/MiuiClock                 com/android/systemui/statusbar/views/NetworkSpeedView
com/miui/clock/classic/ClassicTextAreaView                     com/miui/clock/module/ClockBean
com/miui/systemui/notification/MiuiBaseNotifUtil               com/miui/systemui/shade/header/ShadeHeaderClipController
com/miui/systemui/util/ScenarioRecognitionEventUtils           com/miui/systemui/widget/CircleAndTickAnimView
com/xiaomi/onetrack/f/a
```

零散改动：`HDController.isVisible` -1、`ScenarioRecognitionEventUtils` 新增静态 volatile 字段 `sFaceUnlockStartTime` / `sFingerprintUnlockStartTime`（人脸/指纹解锁耗时埋点）、`com/xiaomi/onetrack/f/a` 新增静态字段 `f`（统计 SDK）、`CircleAndTickAnimView.onDraw` 等长替换（清除按钮绘制）、`MiuiKeyguardBlurInteractor` -18（锁屏模糊比例逻辑）。

## 6. 中文文案改动（会直接体现在界面上）

| 键 | 原版 | 改版 |
|---|---|---|
| `quick_settings_miui_wifi_label` | WLAN | 无线局域网 |
| `quick_settings_miui_wlan_label` | WLAN | 无线局域网 |
| `quick_settings_cellular_detail_title` | 移动数据 | 蜂窝数据 |
| `keyguard_num_state_zen_mode_text` | 勿扰 | 勿扰默认 |
| `face_unlock_fail_retry_global` | 点击图标使用人脸解锁 | **击图标使用人脸解锁**（原文缺字，疑似误改） |

## 7. 风险与已知失效点

1. **未重签 + v3 摘要不匹配**：只能整包塞系统分区（或用保留签名块的装法）。任何「重签再装」都会让 SystemUI 起不来。
2. **`resources.arsc` 结构越界**：aapt / aapt2 无法解析改版，后续若要做资源级二次修改，工具链会先失败。
3. **「清除全部」硬坐标 `translationX=158dp / translationY=-550dp`**：分辨率、字号、显示大小一变就偏位。
4. **`-xxhdpi` 全量 ×1.0909**：2400×1080 上控制中心整体放大 9%，换到别的密度档没有任何适配值（改版只补了 `-xxxhdpi`）。
5. **`IosLeftIcons` 的左右判定依赖 View 实例**：`inGroup` 用引用比较，Compose 包装层插入后可能误判，表现为图标跳色或错位。
6. **`PhoneStatusBarView.dispatchTouchEvent` 无条件先跑手势判定**：时钟区 16dp 阈值内的滑动会被吞掉，时钟长按（秒开关）与原生长按事件可能冲突。
7. **`NumPadKey.drawableStateChanged` 删掉了原 Folme 按压块（-12 行）**：原按键按压动效由 `LockscreenPinGlass` 接管，两者若同时生效会抢属性。
8. **`data_type_name_default_value` 的 `5Gᴀ`**：用的是小体大写字母 U+1D00，不是 `A`，某些字体下会渲染成方框。

## 8. 复现

```bash
export JAVA_OPTS="-Xmx4g"
apktool d -f --no-debug-info -o A "系统界面_17.03.260226.r.apk"
apktool d -f --no-debug-info -o B "MiuiSystemUI.apk"

python3 scripts/zipdiff.py A.apk B.apk        # ZIP 条目层
python3 scripts/index_classes.py A B data      # 类级 md5 索引
DIFF_A=A DIFF_B=B DIFF_DATA=data python3 scripts/analyze_methods.py   # 归一化方法级
DIFF_A=A DIFF_B=B DIFF_DATA=data python3 scripts/vals_compare.py      # 资源集合
```

判读口径见 [docs/03-复现与口径.md](docs/03-复现与口径.md)。

## 9. 仓库内容

```
README.md                 本文件：总结论 + 逐组明细
docs/01-代码层.md          53 个改动类 × 方法级清单
docs/02-资源层.md          layout / values / drawable 全量差异
docs/03-复现与口径.md      工具版本、归一化规则、误报来源
data/                      原始比对数据（类清单、方法级 tsv、资源 diff）
scripts/                   可复现脚本
记录/                      本次审计的过程记录（四行头 + 结论 + 产物索引）
```

## 10. 结论分层

- **已确认**（有工具输出或字节比对）：大小 / 哈希 / 签名未变 / Manifest 未变 / 57 新增类 / 53 真实改动类 / 67 改动方法 / 124 新增 values 键 / 41 新增 public id / 全部 dimens 与颜色数值。
- **假设**（由代码与布局推断，未上机验证）：每个模块的实际视觉表现、手势阈值的手感、控制中心放大 9% 后的布局是否会重叠。
- **未验证**：改版在非 2400×1080 设备上的表现；`5Gᴀ` 字符在各字体下的渲染；`IosLeftIcons` 在 Compose 重排后的稳定性。

---

作者 Mcool｜酷安 @槑さん｜QQ 群 1132120965

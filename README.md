# Blender-CM3D2-Converter
　3Dアダルトゲーム「[カスタムメイド3D2](http://kisskiss.tv/cm3d2/)」で使用されるモデルファイル形式(.model)を  
　フリー3D統合環境である「[Blender](https://www.blender.org/)」で扱うためのアドオンです。  
　ある程度Blenderの基本操作をできる人を対象にしています、  
　初めての人は[チュートリアル](https://www.google.co.jp/#q=Blender+%E3%83%81%E3%83%A5%E3%83%BC%E3%83%88%E3%83%AA%E3%82%A2%E3%83%AB)などから始めましょう。  

## インストール (Installation)
　まず、Blender2.7以上([2.75](http://download.blender.org/release/Blender2.75/)推奨)がインストールされており[日本語化](http://ch.nicovideo.jp/hiiragik/blomaga/ar501365)している事が前提です。  
　画面右の「[Download ZIP](https://github.com/CM3Duser/Blender-CM3D2-Converter/archive/master.zip)」からファイルをダウンロード・解凍し、  
　Windows7なら「C:\Users\ユーザー名\AppData\Roaming\Blender Foundation\  
　Blender\2.75\scripts\addons\CM3D2 Converter\～.py」となるように配置してください。  
　![配置](http://i.imgur.com/QvbMDR1.jpg)  
　Blenderを起動しユーザー設定のアドオンタブで「cm3d」等で検索、  
　「Import-Export: CM3D2 Converter」をオンにすれば一時的に有効になります。  
　次回起動時からも有効にしておきたい場合は「ユーザー設定の保存」をクリックして下さい。  
　![有効化](http://i.imgur.com/6jmFWxQ.jpg)  
　一度インストールしてしまえば、アドオン設定画面かヘルプメニューからアップデート可能です。  
　![更新](http://i.imgur.com/3c0avlw.jpg)  
　更新が気になる人は[RSS](https://github.com/CM3Duser/Blender-CM3D2-Converter/commits/master.atom)への登録もどうぞ。  

## 使い方 (How to Use)
　.modelファイルは「model.arc」や「model2.arc」から[CM3D2 Tool](http://www.hongfire.com/forum/showthread.php/445616)等で取り出しておいて下さい。  
　  
　読み込みは  
　　ファイル > インポート > CM3D2 Model (.model)  
　書き出しも同じように  
　　ファイル > エクスポート > CM3D2 Model (.model)  
　![手順](http://i.imgur.com/p2V7D5m.jpg)  
　どちらも、ファイル選択時の左下にオプションがあります。  

## メモ (Note)

### ボーン
　ボーン情報は「BoneData」と「LocalBoneData」というテキストデータ、  
　![テキスト](http://i.imgur.com/pvgSZy5.jpg)  
　もしくは、オブジェクトかアーマチュアデータ内のカスタムプロパティに保存されています。  
　![カスタムプロパティ](http://i.imgur.com/HHzvdAK.jpg)  
　テキストならボーン情報を編集しやすく、カスタムプロパティなら  
　1つのblendファイルに複数のボーン情報を保持できるというメリットがあります。  
　これらを編集すればボーン設定を変更することも可能ですが、慣れない内は変えない事をおすすめします。  
　エクスポート時にどれを参照するかを選ぶ事が可能です。  

### オブジェクト
　オブジェクト名は必ず「name.bone」のように、「.(ピリオド)」で区切った形式にして下さい。  
　前半がmodel名、後半がメッシュの位置のベースになるボーンの名前です。  
　![オブジェクト名エラー](http://i.imgur.com/lnLydVO.jpg)  
　読み込んだモデルによってはオブジェクトの中心点が3D空間の中心とズレている場合があります。  
　その場合は出力時にもその位置に中心点を合わせてからエクスポートして下さい。  

### メッシュ
　四角ポリゴンがあっても自動で三角ポリゴンに変換して出力しますが、手動で三角化した方が綺麗です。  
　五角ポリゴン以上は無視されるので、必ず四角か三角ポリゴンに変換して下さい。  
　ウェイトが割り当てられていない頂点があった場合、エラーを出して中止します。  
　ウェイト値の合計が1.0でなくても、エクスポート時に自動的に調整します。  
　ウェイトの数が5つ以上でも、自動的に割り当てが大きい順で4つ選ばれます。  
　頂点数は65535程度に抑えたほうが無難です。  
　  
　シェイプキーのあるメッシュにモディファイアを適用するには[このアドオン](https://sites.google.com/site/matosus304blendernotes/home/download#apply_modifier)を使用して下さい。  

### マテリアル
　マテリアル情報は、マテリアルとテクスチャと画像の設定値によって保管しています。  
　シェーダー(CM3D2/Toony_Lighted_Outlineなど)は、  
　マテリアルのカスタムプロパティ「shader1」「shader2」で変更可能です。  
　![カスタムプロパティ](http://i.imgur.com/5fFEcw9.jpg)  
　  
　またマテリアル情報をテキストでも保管しているので(名前は「Material:0」等)出力時に設定を変えれば  
　そちらを参照する事も可能です。自分が編集しやすい方を活用して下さい。  
　  
　インポート時にマテリアルに色がつきますが、エクスポート時には関係ありません。  

### テクスチャ
![テクスチャ群](http://i.imgur.com/UNerNpl.jpg)  
#### 設定値の一例
##### 　　_MainTex
###### 　　　　面の色を決めるテクスチャ。
##### 　　_ShadowTex
###### 　　　　面が陰になった部分の色を決めるテクスチャ。
##### 　　_Color
###### 　　　　追加の色。おそらく乗算なので白で無効。
##### 　　_ShadowColor
###### 　　　　影になった部分の色。おそらく乗算なので白で無効。
##### 　　_RimColor
###### 　　　　メッシュの縁にできる反射光の色。黒で無効。
##### 　　_OutlineColor
###### 　　　　輪郭線の色。
##### 　　_Shininess
###### 　　　　光沢の強さ(Blenderでいうスペキュラー)。
##### 　　_OutlineWidth
###### 　　　　輪郭線の太さ。
##### 　　_RimPower
###### 　　　　メッシュの縁にできる反射光の濃さ・強度。
##### 　　_RimShift
###### 　　　　メッシュの縁にできる反射光の幅。
#### テクスチャタイプの見分け方
##### 　テクスチャが有効
###### 　　「tex」タイプの設定値です、「テクスチャ名」「画像名」  
###### 　　「画像のパス」「デフォルトカラー」「カラー強度」などで変更。
##### 　テクスチャが無効で、「RGBを強度に変換」が有効
###### 　　「col」タイプの設定値です、「テクスチャ名」「デフォルトカラー」「カラー強度」などで変更。
##### 　テクスチャが無効で、「RGBを強度に変換」が無効
###### 　　「f」タイプの設定値です、「テクスチャ名」「カラー強度」などで変更。  
![テクスチャ設定](http://i.imgur.com/6WuW6jI.jpg)  

### その他
　元の.modelに上書きする必要はありません。  
　データ名が「○○.001」のように末尾に連番が付いていても自動的に削除されます。  

## おまけツール (Misc Tools)
　　このアドオンで追加された機能はアイコン![専用アイコン](http://i.imgur.com/Sey1kBN.jpg)で統一されています。  
### CM3D2用マテリアルを新規作成
　　このアドオンで使える仕様のマテリアルを新規作成できます。  
　　「マテリアル」タブ > 「CM3D2用マテリアルを新規作成」ボタン。  
　　出来るだけ汎用的な初期値にしていますが、細かい調整は必要になると思われます。  
　　![CM3D2用マテリアルを新規作成](http://i.imgur.com/l6TgmhY.jpg)
### クイック・ウェイト転送
　　メッシュデータの転送(ウェイト転送)を使いやすくしたものです。  
　　参考にするモデル → 割り当てるモデル の順で選択し、  
　　「メッシュデータ」タブ > 「頂点グループ」パネル > 「▼」ボタン > 「クイック・ウェイト転送」ボタン。  
　　オプションを変更しなければ、不要な頂点グループを削除してくれます。  
　　![クイック・ウェイト転送](http://i.imgur.com/r7Bq6ux.jpg)  
### 頂点グループぼかし
　　頂点グループ(ウェイト)をぼかしてスムーズにします。  
　　モデルを選択し、「メッシュデータ」タブ > 「頂点グループ」パネル >  
　　>「▼」ボタン > 「頂点グループぼかし」ボタン。  
　　ウェイト転送でコピーしたウェイトがガタガタの時などにどうぞ。  
　　![頂点グループぼかし](http://i.imgur.com/p3HNTVR.jpg)  
### シェイプキー強制転送
　　最も近い面(頂点)からシェイプキーをコピーします。  
　　参考にするモデル → 割り当てるモデル の順で選択し、  
　　「メッシュデータ」タブ > 「シェイプキー」パネル > 「▼」ボタン > 「シェイプキー強制転送」ボタン。  
　　あらかじめ参考にするモデルを分割しておくことで、コピーの精度を上げることが可能です。  
　　![シェイプキー強制転送](http://i.imgur.com/6y1s8Vd.jpg)  
### シェイプキーの変形を拡大/縮小
　　シェイプキーの変形を強くしたり、もしくは弱くできます。  
　　モデルを選択し「メッシュデータ」タブ > 「シェイプキー」パネル >  
　　> 「▼」ボタン > 「シェイプキーの変形を拡大/縮小」ボタン。  
　　シェイプキーを転送したにも関わらず身体が服を突き抜ける場合などに、  
　　これで変形を大きくすると修正できるかもしれません。  
　　![シェイプキーの変形を拡大/縮小](http://i.imgur.com/vw9NO6Z.jpg)  
### シェイプキーをぼかす
　　シェイプキーの変形をぼかしてスムーズにします。  
　　モデルを選択し「メッシュデータ」タブ > 「シェイプキー」パネル >  
　　> 「▼」ボタン > 「シェイプキーをぼかす」ボタン。  
　　「シェイプキー強制転送」でコピーした変形がガタガタの時などにどうぞ。  
　　![シェイプキーをぼかす](http://i.imgur.com/P69O44k.jpg)  
### ボーン/頂点グループ名をCM3D2用←→Blender用に変換
　　ボーンと頂点グループの名前をBlenderで左右対称編集できるように変換したり元に戻せます。  
　　メッシュを選択し「メッシュデータ」タブ > 「頂点グループ」パネル >  
　　> 「▼」ボタン > 「頂点グループ名を～」ボタン。  
　　もしくはアーマチュアを選択し「アーマチュアデータ」タブ > 「ボーン名を～」ボタン。  
　　![ボーン/頂点グループ名をCM3D2用←→Blender用に変換](http://i.imgur.com/6O5K5gm.jpg)

## 規約 (Agreement)
[公式のMOD規約](http://kissdiary.blog11.fc2.com/blog-entry-577.html)を厳守して下さい。  

## .modelのフォーマット (.model Format)
* (String) 「CM3D2_MESH」固定
* (Int) バージョン番号
* (String) モデル名
* (String) 基点ボーン名
* (Int) ボーン数
* for ボーン数
	- (String) ボーン名
	- (Char) フラグ？
* for ボーン数
	- (Int) 親番号
* for ボーン数
	- (Float×3) ボーン位置
	- (Float×4) ボーン回転
* (Int) 頂点数
* (Int) メッシュ数 (マテリアル数)
* (Int) 使用ボーン数
* for 使用ボーン数
	- (String) ボーン名
* for 使用ボーン数
	- (Float×16) ボーン変換行列
* for 頂点数
	- (Float×3) 頂点位置
	- (Float×3) 法線方向
	- (Float×2) UV位置
* (Int) 不明な数 (0もしくは頂点数と同じ)
* for 不明な数
	- (Float×4) 不明な数値
* for 頂点数
	- (Short×4) 割り当てるボーン番号×4
	- (Float×4) 割り当てるウェイト×4
* for メッシュ数
	- (Int) 面数
	- for 面数
		* (Short) 頂点番号
* (Int) マテリアル数 (メッシュ数)
* for マテリアル数
	- (String) マテリアル名
	- (String) 使用シェーダー
	- (String) 使用シェーダー
	- while
		* (String) 設定値タイプ
		* if 設定値タイプ == "tex"
			- (String) テクスチャ名
			- (String) テクスチャタイプ
			- if テクスチャタイプ == "tex2d"
				* (String) 画像名
				* (String) 画像パス
				* (Float×4) 色 (RGBA)
		* else if 設定値タイプ == "col"
			- (String) 色名
			- (Float×4) 色 (RGBA)
		* else if 設定値タイプ == "f"
			- (String) 値名
			- (Float) 値
		* else if 設定値タイプ == "end"
			- break
* while
	- (String) 設定値タイプ
	- if 設定値タイプ == "morph"
		* (String) モーフ名
		* (Int) 変更頂点数
		* for 変更頂点数
			- (Short) 頂点番号
			- (Float×3) 頂点位置
			- (Float×3) 法線方向
	- else if 設定値タイプ == "end"
		* break

## 課題 (Assignment)
* 一部のmodelに含まれる「頂点数xFloatx4」分のデータを解析、入出力可能に
* ボーン情報を人力で編集可能な形にする
* モーションファイル(.anm)の読み込み対応

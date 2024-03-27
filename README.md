<!-- TODO: APIドキュメントを生成するかどうか考える -->
<!-- # [API Documentation](https://luvoid.github.io/Blender-CM3D2-Converter/)

[https://luvoid.github.io/Blender-CM3D2-Converter](https://luvoid.github.io/Blender-CM3D2-Converter/) ([Translated](https://luvoid-github-io.translate.goog/Blender-CM3D2-Converter/index.html?_x_tr_sl=auto&_x_tr_tl=default)) -->

# Blender-Ryokusasa-Addon

<!-- [Blender-CM3D2-Converter](https://github.com/luvoid/Blender-CM3D2-Converter) から CM3D2 関連の機能を取り除いたもの -->

**注意点**

- Blender の便利機能を追加するアドオンです

## 目次

- [インストール](#インストール)
- [使い方](#使い方)
- [機能一覧](#機能一覧)
- [規約](#規約)
- [model のフォーマット](#modelのフォーマット)
- [課題](#課題)

## インストール

画面右上の緑色の「Clone or download」→「[Download ZIP](https://github.com/Ryokusa/Blender-R-addons/archive/bl_28.zip)」からファイルをダウンロード・解凍し、  
　 「~\addons\BR addon\＊.py」となるように配置してください。
一度インストールしてしまえば、アドオン設定画面かヘルプメニューからアップデート可能です。

## 使い方

未定

## おまけツール (Misc Tools)

このアドオンで追加された機能は以下のアイコンで統一されています。
![専用アイコン](<BR Addon/kiss.png>)

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

### ボーン/頂点グループ名を CM3D2 用 ←→Blender 用に変換

ボーンと頂点グループの名前を Blender で左右対称編集できるように変換したり元に戻せます。  
　　メッシュを選択し「メッシュデータ」タブ > 「頂点グループ」パネル >  
　　> 「▼」ボタン > 「頂点グループ名を～」ボタン。  
　　もしくはアーマチュアを選択し「アーマチュアデータ」タブ > 「ボーン名を～」ボタン。  
　　![ボーン/頂点グループ名をCM3D2用←→Blender用に変換](http://i.imgur.com/6O5K5gm.jpg)

## 機能一覧

- 「プロパティ」エリア → 「モディファイア」タブ
  - モディファイア強制適用
    - シェイプキーのあるメッシュのモディファイアでも強制的に適用します
- 「UV/画像エディター」エリア → ヘッダー
- 「UV/画像エディター」エリア → プロパティ → 「画像」パネル
- 「3D ビュー」エリア → 追加(Shift+A) → カーブ
  - 髪の房を追加
    - アニメ調の髪の房を追加します
- 画面上部 (「情報」エリア → ヘッダー) → ヘルプ
  - アドオンを更新
    - GitHub から最新版のアドオンをダウンロードし上書き更新します
  - アドオン設定画面を開く
    - アドオンの設定画面を表示します
- 「プロパティ」エリア → 「メッシュデータ」タブ → 「シェイプキー」パネル → ▼ ボタン
  - クイック・シェイプキー転送
    - アクティブなメッシュに他の選択メッシュのシェイプキーを高速で転送します
  - 空間ぼかし・シェイプキー転送
    - アクティブなメッシュに他の選択メッシュのシェイプキーを遠いほどぼかして転送します
  - シェイプキーの変形に乗算
    - シェイプキーの変形に数値を乗算し、変形の強度を増減させます
  - シェイプキーぼかし
    - アクティブ、もしくは全てのシェイプキーをぼかします
  - このシェイプキーをベースに
    - アクティブなシェイプキーを他のシェイプキーのベースにします
  - Vertex Groups Selector
  - Weighted shape key transfer
    - Transfers the shape keys of other selected mesh to the active mesh, using matching vertex groups as masks
  - Copy shape key values
    - Copy the shape key values from the other selected mesh
- 「プロパティ」エリア → 「メッシュデータ」タブ → 「頂点グループ」パネル → ▼ ボタン
  - クイック・ウェイト転送
    - アクティブなメッシュに他の選択メッシュの頂点グループを高速で転送します
  - 空間ぼかし・ウェイト転送
    - アクティブなメッシュに他の選択メッシュの頂点グループを遠いほどぼかして転送します
  - 頂点グループぼかし
    - アクティブ、もしくは全ての頂点グループをぼかします
  - 旧・頂点グループぼかし
    - アクティブ、もしくは全ての頂点グループをぼかします
  - 頂点グループに乗算
    - 頂点グループのウェイトに数値を乗算し、ウェイトの強度を増減させます
  - 割り当てのない頂点グループを削除
    - どの頂点にも割り当てられていない頂点グループを全て削除します
- 「プロパティ」エリア → 「オブジェクト」タブ → 「トランスフォーム」パネル
  - オブジェクトの位置を合わせる
    - アクティブオブジェクトの中心位置を、他の選択オブジェクトの中心位置に合わせます
- 「3D ビュー」エリア → メッシュ編集モード → 「W」キー
  - 選択面の描画順を最前面に
    - 選択中の面の描画順を最も前面/背面に並び替えます
- 「3D ビュー」エリア → 「ウェイトペイント」モード → ツールシェルフ → 「ウェイトツール」パネル

  - 選択部の頂点グループをぼかす
    - 選択メッシュの頂点グループの割り当てをぼかします
  - 選択部の頂点グループに四則演算
    - 選択メッシュの頂点グループの割り当てに四則演算を施します

- VIEW3D_MT_edit_mesh_splits
  - Split Sharp Edges
- VIEW3D_MT_pose_apply
  - Copy Prime Field
- MESH_MT_attribute_context_menu
  - From Custom Normals
    - Creates a new attribute from the custom split normals
  - Convert Normals
    - Converts the data type of the normals attribute

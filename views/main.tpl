<!DOCTYPE html>
<html lang="ja">

    <head>
        <meta charset="UTF-8">
        <title>画像</title>
        <link rel="stylesheet" href="/css/style.css" media="all"/>
    </head>

    <body id="service">

        <header>
            <a href="/"><img src="/img/logo1.png" class="logo"></a>
        </header>

        <div class="show-image">
            <a href = {{mvdict["next"]}}><img src={{!img}} class="ex-image"></a>
        </div>

        <div class="operator">
            <a href = {{mvdict["back"]}}><img src="/img/back.png" class="op-img"/></a>
            <a href = {{mvdict["pagetop"]}}><img src="/img/top.png" class="op-img"/></a>
            <a href = {{mvdict["next"]}}><img src="/img/next.png" class="op-img"/></a>
        </div>

    </body>
</html>

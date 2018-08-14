<!DOCTYPE html>
<html lang="ja">

    <head>
        <meta charset="UTF-8">
        <title>一覧</title>
        <link rel="stylesheet" href="/css/style.css" media="all"/>
    </head>

    <body id="service">

        <header>
            <a href="/"><img src="/img/logo1.png" class="logo"></a>
        </header>

        <div class="items">

            <div class="directory">
                % for name, path in sorted(dirs.items()):
                <p><a href="/ls/{{path}}">{{name}}</a></p>
                % end
            </div>

            <div class="books">
                % for name, path in sorted(files.items()):
                    <div class="list_outer">
                         <a href="/list/{{path}}/1">
                         <img src="/tmb/{{path}}/0">
                         <p>{{name}}</p>
                         </a>
                     </div>
                % end
            </div>

        </div>

    </body>
</html>

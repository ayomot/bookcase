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

        <div class="thumbnails">
	    % for i in index:
            <div class="tmb_outer">
                <div class="tmb_inner">
                    <a href="/view/{{name}}/{{i}}"><img src="/tmb/{{name}}/{{i}}" class="thumbnail" ></a>
                </div>
            </div>
		% end
        </div>

        <div class="index">
            <table class="page-index">
                <tbody>
                    <tr>
                    % for i in list(table):

                        % if i == p:
                            <td>{{i}}</td>
                        % elif i == "...":
                            <td>{{i}}</td>
                        % else:
                            <td><a href="/list/{{name}}/{{i}}">{{i}}</a></td>
                        % end

                    % end
                    </tr>
                </tbody>
            </table>
        </div>
        <fotter>
            <a href="/ls/{{base}}">戻る</a>
        </fotter>

    </body>
</html>

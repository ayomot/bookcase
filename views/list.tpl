% rebase("layout.tpl", title="ページ一覧")
<div class="thumbnails">
% for i in index:
	<div class="tmb_outer">
	<a href="/view/{{name}}/{{i}}" class="tmb_inner"><img src="/tmb/{{name}}/{{i}}" class="thumbnail" ></a>
	</div>
% end
</div>

<div class="index">
	<table class="page-index">
		<tbody>
			<tr>
			% for i in list(table):

				% if i == str(p) or i == "...":
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

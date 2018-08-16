% rebase("layout.tpl", title="書籍一覧")
<div class="items">

	<div class="directorys">
		% for name, path in sorted(dirs.items()):
		<div class="list_outer">
			<a href="/ls/{{path}}">
			<img src="/img/directory.png">
			<p>{{name}}</p>
			</a>
		</div>
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

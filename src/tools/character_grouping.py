from unionfind import unionfind


class CharacterGrouping:
    def __init__(self, names: list) -> None:
        self.num_char_dict = {}
        self.char_num_dict = {}
        self.uf = unionfind(len(names))

        # assign each character a number in the union find
        for i, name in enumerate(names):
            self.num_char_dict[i] = name
            self.char_num_dict[name] = i

    def convert_to_num(self, name_idx) -> int:
        if type(name_idx) is str:
            name_idx = self.char_num_dict[name_idx]
        return name_idx

    def convert_to_name(self, name_idx) -> str:
        if type(name_idx) is int:
            name_idx = self.num_char_dict[name_idx]
        return name_idx

    def unite(self, name_idx_1, name_idx_2) -> None:
        # convert name into an index
        name_idx_1 = self.convert_to_num(name_idx_1)
        name_idx_2 = self.convert_to_num(name_idx_2)
        self.uf.unite(name_idx_1, name_idx_2)

    def find(self, name_idx) -> str:
        name_idx = self.convert_to_num(name_idx)
        parent_idx = self.uf.find(name_idx)
        return self.num_char_dict[parent_idx]

    def issame(self, name_idx_1, name_idx_2) -> bool:
        return self.find(name_idx_1) == self.find(name_idx_2)

    def groups(self) -> list[list[str]]:
        groups = self.uf.groups()
        for i, l in enumerate(groups):
            for j, e2 in enumerate(l):
                groups[i][j] = self.num_char_dict[e2]
        return groups


if __name__ == '__main__':
    def groupingtest():
        cg = CharacterGrouping([
            "Mike",
            "Emily",
            "Mark",
            "Julia",
            "Max"
        ])
        print(cg.groups())
        cg.unite("Mike", "Mike")
        cg.unite("Julia", 4)    # Max
        print(cg.find(3))   # parent of Julia
        print(cg.groups())

    def unionfindtest():
        u = unionfind(5)
        u.unite(1,1)
        print(u.groups())

    groupingtest()
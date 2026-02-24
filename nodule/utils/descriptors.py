

shape=["irregular","oval","round"]
margin=["angulated","circumscribed","spiculated","indistinct","microlobulated"]
orientation=["parallel","not parallel"]
echogenicity=["anechoic","heterogeneous","hypoechoic","isoechoic","hyperechoic","complex cystic and solid"]
posterior=["enhancement","no features","shadowing", "combined pattern"]
# halo=["no halo","halo"]
calcification=["no calcifications","calcifications"]
suggestivity=["simple cyst", "clustered microcysts","complicated cyst", "mass in skin","mass on skin","lymph node","postsurgical fluid collection","fat necrosis"]
shape.sort()
margin.sort()
echogenicity.sort()
orientation.sort()
posterior.sort()
# halo.sort()
calcification.sort()
suggestivity.sort()

birads=["2","3","4A","4B","4C","5"]
birads.sort()

descriptors={"shape":shape,"margin":margin,"orientation":orientation,"echogenicity":echogenicity,"posterior":posterior,"calcification":calcification,"suggestivity":suggestivity,"birads":birads}

word_to_idx_shape = dict((word, idx) for idx, word in enumerate(shape))
idx_to_word_shape = dict((idx, word) for idx, word in enumerate(shape))

word_to_idx_margin = dict((word, idx) for idx, word in enumerate(margin))
idx_to_word_margin = dict((idx, word) for idx, word in enumerate(margin))

word_to_idx_orientation = dict((word, idx) for idx, word in enumerate(orientation))
idx_to_word_orientation = dict((idx, word) for idx, word in enumerate(orientation))

word_to_idx_echogenicity = dict((word, idx) for idx, word in enumerate(echogenicity))
idx_to_word_echogenicity = dict((idx, word) for idx, word in enumerate(echogenicity))

word_to_idx_posterior = dict((word, idx) for idx, word in enumerate(posterior))
idx_to_word_posterior = dict((idx, word) for idx, word in enumerate(posterior))

# word_to_idx_halo = dict((word, idx) for idx, word in enumerate(halo))
# idx_to_word_halo = dict((idx, word) for idx, word in enumerate(halo))
word_to_idx_calcification = dict((word, idx) for idx, word in enumerate(calcification))
idx_to_word_calcification = dict((idx, word) for idx, word in enumerate(calcification))

word_to_idx_suggestivity = dict((word, idx) for idx, word in enumerate(suggestivity))
idx_to_word_suggestivity = dict((idx, word) for idx, word in enumerate(suggestivity))

word_to_idx_birads = dict((word, idx) for idx, word in enumerate(birads))
idx_to_word_birads = dict((idx, word) for idx, word in enumerate(birads))

word_to_idx_field={"shape":word_to_idx_shape,"margin":word_to_idx_margin,"orientation":word_to_idx_orientation,"echogenicity":word_to_idx_echogenicity,"posterior":word_to_idx_posterior,"calcification":word_to_idx_calcification,"suggestivity":word_to_idx_suggestivity,"birads":word_to_idx_birads}
idx_to_word_field={"shape":idx_to_word_shape,"margin":idx_to_word_margin,"orientation":idx_to_word_orientation,"echogenicity":idx_to_word_echogenicity,"posterior":idx_to_word_posterior,"calcification":idx_to_word_calcification,"suggestivity":idx_to_word_suggestivity,"birads":idx_to_word_birads}
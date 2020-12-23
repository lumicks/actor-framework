/******************************************************************************
 *                       ____    _    _____                                   *
 *                      / ___|  / \  |  ___|    C++                           *
 *                     | |     / _ \ | |_       Actor                         *
 *                     | |___ / ___ \|  _|      Framework                     *
 *                      \____/_/   \_|_|                                      *
 *                                                                            *
 * Copyright 2011-2018 Dominik Charousset                                     *
 *                                                                            *
 * Distributed under the terms and conditions of the BSD 3-Clause License or  *
 * (at your option) under the terms and conditions of the Boost Software      *
 * License 1.0. See accompanying files LICENSE and LICENSE_ALTERNATIVE.       *
 *                                                                            *
 * If you did not receive a copy of the license files, see                    *
 * http://opensource.org/licenses/BSD-3-Clause and                            *
 * http://www.boost.org/LICENSE_1_0.txt.                                      *
 ******************************************************************************/

#include "caf/make_config_option.hpp"

#include <ctype.h>

#include "caf/config_value.hpp"
#include "caf/optional.hpp"

namespace caf {

namespace {

using meta_state = config_option::meta_state;

error bool_sync_neg(void* ptr, config_value& x) {
  if (auto val = get_as<bool>(x)) {
    x = config_value{*val};
    if (ptr)
      *static_cast<bool*>(ptr) = !*val;
    return none;
  } else {
    return std::move(val.error());
  }
}

config_value bool_get_neg(const void* ptr) {
  return config_value{!*static_cast<const bool*>(ptr)};
}

meta_state bool_neg_meta{bool_sync_neg, bool_get_neg,
                         detail::config_value_access_t<bool>::type_name()};

template <uint64_t Denominator>
error sync_timespan(void* ptr, config_value& x) {
  if (auto val = get_as<timespan>(x)) {
    x = config_value{*val};
    if (ptr)
      *static_cast<size_t*>(ptr) = static_cast<size_t>(get<timespan>(x).count())
                                   / Denominator;
    return none;
  } else {
    return std::move(val.error());
  }
}

template <uint64_t Denominator>
config_value get_timespan(const void* ptr) {
  auto ival = static_cast<int64_t>(*static_cast<const size_t*>(ptr));
  timespan val{ival * Denominator};
  return config_value{val};
}

meta_state us_res_meta{sync_timespan<1000>, get_timespan<1000>,
                       detail::config_value_access_t<timespan>::type_name()};

meta_state ms_res_meta{sync_timespan<1000000>, get_timespan<1000000>,
                       detail::config_value_access_t<timespan>::type_name()};

} // namespace

config_option make_negated_config_option(bool& storage, string_view category,
                                         string_view name,
                                         string_view description) {
  return {category, name, description, &bool_neg_meta, &storage};
}

config_option
make_us_resolution_config_option(size_t& storage, string_view category,
                                 string_view name, string_view description) {
  return {category, name, description, &us_res_meta, &storage};
}

config_option
make_ms_resolution_config_option(size_t& storage, string_view category,
                                 string_view name, string_view description) {
  return {category, name, description, &ms_res_meta, &storage};
}

} // namespace caf

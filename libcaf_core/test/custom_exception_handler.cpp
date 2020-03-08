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

#include "caf/config.hpp"

#define CAF_SUITE custom_exception_handler
#include "caf/test/unit_test.hpp"

#include "caf/all.hpp"

using namespace caf;

#ifndef CAF_NO_EXCEPTIONS

class exception_testee : public event_based_actor {
public:
  ~exception_testee() override;
  exception_testee(actor_config& cfg) : event_based_actor(cfg) {
    set_exception_handler([](std::exception_ptr&) -> error {
      return exit_reason::remote_link_unreachable;
    });
  }

  behavior make_behavior() override {
    return {
      [](const std::string&) {
        throw std::runtime_error("whatever");
      }
    };
  }
};

exception_testee::~exception_testee() {
  // avoid weak-vtables warning
}

CAF_TEST(test_custom_exception_handler) {
  actor_system_config cfg;
  actor_system system{cfg};
  auto handler = [](std::exception_ptr& eptr) -> error {
    try {
      std::rethrow_exception(eptr);
    }
    catch (std::runtime_error&) {
      return exit_reason::normal;
    }
    catch (...) {
      // "fall through"
    }
    return exit_reason::unhandled_exception;
  };
  scoped_actor self{system};
  auto testee1 = self->spawn<monitored>([=](event_based_actor* eb_self) {
    eb_self->set_exception_handler(handler);
    throw std::runtime_error("ping");
  });
  auto testee2 = self->spawn<monitored>([=](event_based_actor* eb_self) {
    eb_self->set_exception_handler(handler);
    throw std::logic_error("pong");
  });
  auto testee3 = self->spawn<exception_testee, monitored>();
  self->send(testee3, "foo");
  // receive all down messages
  self->wait_for(testee1, testee2, testee3);
}

CAF_TEST(test_exception_recovery) {
  actor_system_config cfg;
  actor_system system{cfg};
  auto exception_handler = [](std::exception_ptr& eptr) -> error {
    try {
      std::rethrow_exception(eptr);
    } catch (std::runtime_error&) {
      return sec::runtime_error;
    } catch (std::logic_error&) {
      return sec::none;
    } catch (...) {
      return exit_reason::unhandled_exception;
    }
  };
  auto error_handler = [](scheduled_actor* ptr, const error& err) {
    if (err) {
      ptr->quit(err);
    }
  };

  scoped_actor self{system};
  using throw_atom = atom_constant<atom("throw")>;
  auto testee1 = self->spawn<monitored>([=](event_based_actor* eb_self) {
    eb_self->set_exception_handler(exception_handler);
    eb_self->set_error_handler(error_handler);
    return caf::behavior([](throw_atom) -> int {
      throw std::runtime_error("ping");
    });
  });
  auto testee2 = self->spawn<monitored>([=](event_based_actor* eb_self) {
    eb_self->set_exception_handler(exception_handler);
    eb_self->set_error_handler(error_handler);
    return caf::behavior([](throw_atom) -> int {
      throw std::logic_error("pong");
    });
  });

  auto check_error = [&](const actor& a, const error& expected) {
    self->request(a, infinite, throw_atom::value)
      .receive([](int i) { CAF_FAIL(i); },
               [&](const error& e) { CAF_CHECK_EQUAL(e, expected); });
  };

  check_error(testee1, sec::runtime_error);
  check_error(testee1, sec::request_receiver_down);
  check_error(testee2, sec::none);
  check_error(testee2, sec::none);

  anon_send_exit(testee2, exit_reason::kill);
  self->wait_for(testee1, testee2);
}

#else // CAF_NO_EXCEPTIONS

CAF_TEST(no_exceptions_dummy) {
  CAF_CHECK_EQUAL(true, true);
}

#endif // CAF_NO_EXCEPTIONS
